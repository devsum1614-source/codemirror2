import os
import json
import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

from app.database import init_db, get_db
from app.auth import create_session
from app.seed_data import seed_database
from app.seed_challenges import seed_quest_data
from app.runner import run_tests_for_mission
from app.ai_coach import get_staged_hint
from app.routes_v1 import router as v1_router
from app.routes_admin import router as admin_router

# Initialize database and seeds on startup
init_db()
seed_database()
seed_quest_data()

app = FastAPI(
    title="Student Coding Quest API",
    description="Data server and database backend for student coding challenges, AI hints, and game rewards",
    version="1.0.0"
)

@app.middleware("http")
async def disable_static_cache(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static") or request.url.path in ("/login", "/admin", "/admin/login", "/languages"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount versioned API routes
app.include_router(v1_router)
app.include_router(admin_router)

@app.get("/health")
def root_health():
    """Service health only; never exposes database details or secrets."""
    return {
        "status": "ok",
        "service": "student-coding-quest-api",
        "version": "1.0.0"
    }

# Pydantic schemas
class SaveCodeRequest(BaseModel):
    code: str

class RunTestsRequest(BaseModel):
    code: str

class SubmitMissionRequest(BaseModel):
    code: str
    explanation: Optional[str] = ""

class AskCoachRequest(BaseModel):
    code: str
    question: str

# ----------------- REST API Endpoints -----------------

@app.get("/api/user")
def get_user_profile():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
    user = cursor.fetchone()
    
    # Calculate stats
    cursor.execute("SELECT COUNT(*) as total_completed FROM project_missions WHERE status = 'completed'")
    completed_count = cursor.fetchone()["total_completed"]

    cursor.execute("SELECT AVG(score) as avg_score FROM project_missions WHERE status = 'completed'")
    avg_score_row = cursor.fetchone()
    avg_score = round(avg_score_row["avg_score"] or 0, 1)

    cursor.execute("SELECT COUNT(*) as total_evidence FROM skill_evidence")
    evidence_count = cursor.fetchone()["total_evidence"]

    conn.close()
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "streak_days": 3,
        "completed_count": completed_count,
        "readiness_score": int(avg_score) if avg_score > 0 else 78,
        "points": completed_count * 50 + 25,
        "evidence_count": evidence_count
    }


@app.get("/api/projects")
def list_projects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"projects": projects}


@app.get("/api/missions")
def list_missions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.mission_id, m.title, m.track, m.language, m.difficulty, 
            m.file_path, pm.status, pm.score, pm.completed_at
        FROM missions m
        LEFT JOIN project_missions pm ON m.mission_id = pm.mission_id
    """)
    missions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"missions": missions}


@app.get("/api/missions/{mission_id}")
def get_mission_detail(mission_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            m.*, pm.id as pm_id, pm.status, pm.score, pm.student_code, pm.explanation
        FROM missions m
        LEFT JOIN project_missions pm ON m.mission_id = pm.mission_id
        WHERE m.mission_id = ?
    """, (mission_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Mission not found")
    
    data = dict(row)
    data["rubric"] = json.loads(data["rubric_json"]) if data.get("rubric_json") else {}
    if not data.get("student_code"):
        data["student_code"] = data["starter_code"]

    # Retrieve last test run if any
    cursor.execute("""
        SELECT tr.run_id, tr.passed_count, tr.failed_count, tr.duration_ms, tr.created_at
        FROM test_runs tr
        WHERE tr.project_mission_id = ?
        ORDER BY tr.created_at DESC LIMIT 1
    """, (data.get("pm_id"),))
    last_run = cursor.fetchone()
    if last_run:
        data["last_test_run"] = dict(last_run)
        cursor.execute("SELECT * FROM test_results WHERE run_id = ?", (last_run["run_id"],))
        data["last_test_results"] = [dict(r) for r in cursor.fetchall()]
    else:
        data["last_test_run"] = None
        data["last_test_results"] = []

    conn.close()
    return data


@app.post("/api/missions/{mission_id}/save")
def save_mission_code(mission_id: str, req: SaveCodeRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE project_missions SET student_code = ? WHERE mission_id = ?",
        (req.code, mission_id)
    )
    conn.commit()
    conn.close()
    return {"status": "saved", "mission_id": mission_id}


@app.post("/api/missions/{mission_id}/run-tests")
def run_tests(mission_id: str, req: RunTestsRequest):
    # Execute through isolated test engine
    test_report = run_tests_for_mission(mission_id, req.code)

    # Persist test run
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM project_missions WHERE mission_id = ?", (mission_id,))
    pm_row = cursor.fetchone()
    if pm_row:
        pm_id = pm_row["id"]
        cursor.execute("""
            INSERT INTO test_runs (project_mission_id, passed_count, failed_count, duration_ms)
            VALUES (?, ?, ?, ?)
        """, (pm_id, test_report["passed_count"], test_report["failed_count"], test_report["duration_ms"]))
        run_id = cursor.lastrowid

        for res in test_report["results"]:
            cursor.execute("""
                INSERT INTO test_results (run_id, test_name, status, short_message, error_detail)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, res["test_name"], res["status"], res["short_message"], res.get("error_detail")))
        
        # Also update current student code
        cursor.execute(
            "UPDATE project_missions SET student_code = ? WHERE id = ?",
            (req.code, pm_id)
        )
        conn.commit()

    conn.close()
    return test_report


@app.post("/api/missions/{mission_id}/submit")
def submit_mission(mission_id: str, req: SubmitMissionRequest):
    test_report = run_tests_for_mission(mission_id, req.code)
    if not test_report["all_passed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit: {test_report['failed_count']} tests are still failing."
        )

    # Calculate rubric score
    explanation_length = len(req.explanation.strip())
    # Baseline 80% for functional + edge cases + tests passing
    score = 80.0
    if explanation_length >= 25:
        score += 15.0 # Quality explanation bonus
    if "try" in req.code or "if" in req.code:
        score += 5.0 # Defensive code structure

    score = min(score, 100.0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id FROM project_missions WHERE mission_id = ?", (mission_id,))
    pm = cursor.fetchone()
    
    if pm:
        pm_id = pm["id"]
        cursor.execute("""
            UPDATE project_missions 
            SET status = 'completed', score = ?, explanation = ?, completed_at = CURRENT_TIMESTAMP, student_code = ?
            WHERE id = ?
        """, (score, req.explanation, req.code, pm_id))

        # Record skill evidence
        cursor.execute("SELECT title, track FROM missions WHERE mission_id = ?", (mission_id,))
        mission_row = cursor.fetchone()
        skill_name = f"{mission_row['track']} - {mission_row['title']}"

        cursor.execute("""
            INSERT INTO skill_evidence (user_id, skill_name, evidence_type, source_id, score, description)
            VALUES (1, ?, 'mission_verified_tests', ?, ?, ?)
        """, (
            skill_name, 
            mission_id, 
            score, 
            f"Successfully resolved all {test_report['total_count']} automated test assertions. Technical explanation: {req.explanation[:120]}"
        ))

        conn.commit()

    conn.close()
    return {
        "status": "completed",
        "score": score,
        "message": "Mission completed successfully! Skill evidence verified and recorded to SkillProof profile."
    }


@app.get("/api/missions/{mission_id}/hints/{level}")
def fetch_hint(mission_id: str, level: int):
    hint = get_hint(mission_id, level)

    # Record hint query in history
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM project_missions WHERE mission_id = ?", (mission_id,))
    pm = cursor.fetchone()
    if pm:
        cursor.execute("""
            INSERT INTO hint_history (project_mission_id, hint_level, topic, hint_text)
            VALUES (?, ?, ?, ?)
        """, (pm["id"], level, f"Mission {mission_id} - Hint {level}", hint["message"]))
        conn.commit()
    conn.close()

    return hint


@app.post("/api/missions/{mission_id}/ask-coach")
def ask_coach(mission_id: str, req: AskCoachRequest):
    response = explain_code_context(mission_id, req.code, req.question)
    return response


@app.get("/api/skillproof")
def get_skillproof():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            pm.id, pm.mission_id, pm.status, pm.score, pm.completed_at, pm.explanation,
            m.title, m.track, m.language, m.difficulty
        FROM project_missions pm
        JOIN missions m ON pm.mission_id = m.mission_id
        WHERE pm.status = 'completed'
        ORDER BY pm.completed_at DESC
    """)
    completed_missions = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM skill_evidence ORDER BY created_at DESC")
    evidence = [dict(r) for r in cursor.fetchall()]

    # Skill breakdown across tracks
    tracks = {}
    for cm in completed_missions:
        tr = cm["track"]
        if tr not in tracks:
            tracks[tr] = {"count": 0, "total_score": 0}
        tracks[tr]["count"] += 1
        tracks[tr]["total_score"] += cm["score"]

    skill_breakdown = [
        {"track": k, "count": v["count"], "avg_score": round(v["total_score"] / v["count"], 1)}
        for k, v in tracks.items()
    ]

    conn.close()
    return {
        "completed_missions": completed_missions,
        "evidence_records": evidence,
        "skill_breakdown": skill_breakdown,
        "total_verifications": len(evidence)
    }


@app.get("/api/learning-report")
def get_learning_report():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
    user = dict(cursor.fetchone())

    cursor.execute("""
        SELECT pm.*, m.title, m.track, m.language, m.difficulty
        FROM project_missions pm
        JOIN missions m ON pm.mission_id = m.mission_id
        WHERE pm.status = 'completed'
    """)
    completed = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM skill_evidence ORDER BY created_at DESC")
    evidence = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "student": user,
        "institution": "CodeMirror 2.0 Engineering Lab",
        "completed_tasks": completed,
        "evidence": evidence,
        "generated_at": "November 2026",
        "verified_by": "Automated Project-Based Test Harness & AI Rubric Engine"
    }


@app.post("/api/reset-demo")
def reset_demo():
    seed_database()
    return {"status": "success", "message": "Demo data reset to initial starter state."}

# Mount static web UI files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/student")
@app.get("/auto-login/student")
def auto_login_student():
    return _build_auto_login_response("stu_alex_vance", "#dashboard")

@app.get("/admin-console")
@app.get("/auto-login/admin")
def auto_login_admin():
    return _build_auto_login_response("own_master_admin", "#admin")

@app.get("/teacher")
@app.get("/auto-login/teacher")
def auto_login_teacher():
    return _build_auto_login_response("tch_alan_turing", "#admin")

def _build_auto_login_response(account_id: str, target_hash: str) -> HTMLResponse:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ? LIMIT 1", (account_id,))
    account = cursor.fetchone()
    conn.close()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    token = create_session(account["id"], account["role"])
    acc_obj = {
        "id": account["id"],
        "display_name": account["display_name"],
        "email": account["email"],
        "role": account["role"],
        "class_id": account["class_id"]
    }
    acc_json = json.dumps(acc_obj)
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Signing in to Code Wizard...</title></head>
<body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
  <div>Signing in as <strong>{account["display_name"]}</strong>...</div>
  <script>
    localStorage.setItem('cm_session_token', {json.dumps(token)});
    localStorage.setItem('cm_user', JSON.stringify({acc_json}));
    localStorage.setItem('quest_account_id', {json.dumps(account["id"])});
    localStorage.setItem('quest_student_id', {json.dumps(account["id"])});
    window.location.replace('/?login=' + Date.now() + {json.dumps(target_hash)});
  </script>
</body>
</html>"""
    resp = HTMLResponse(content=html)
    resp.set_cookie(key="cm_session", value=token, httponly=True, samesite="lax", max_age=7 * 86400)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/login")
@app.get("/admin")
@app.get("/admin/login")
@app.get("/languages")
@app.get("/languages/{language_id}")
def serve_spa_views(language_id: Optional[str] = None):
    return FileResponse(os.path.join(static_dir, "index.html"))
