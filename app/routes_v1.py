"""
Version 1 REST API Router for Student Coding Quest
Provides endpoints for:
- Health check
- Challenges listing (tests kept private on server)
- Isolated sandbox attempt execution with transactional XP rewards
- Staged progressive hints (Question -> Clue -> Explanation)
- Student progress & level tracking
"""

import uuid
import random
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_optional_account
from app.sandbox import execute_in_sandbox
from app.ai_coach import get_staged_hint, socratic_coach_response, MISSION_MAPPING, is_ai_configured
from app.runtimes import get_available_runtimes, check_language_runtime
from app.languages import get_all_languages_summary, get_language_details

router = APIRouter(prefix="/api/v1")

# Pydantic Request Models
class AttemptRequest(BaseModel):
    challenge_id: str = Field(..., description="ID of the coding challenge")
    code: str = Field(..., description="Student's submitted source code")
    language: Optional[str] = Field("python", description="Programming language of the submission")

class HintRequest(BaseModel):
    challenge_id: str = Field(..., description="ID of the coding challenge")
    current_code: Optional[str] = Field("", description="Student's current editor code")
    error_summary: Optional[str] = Field(None, description="Recent failure summary if available")
    hint_level: int = Field(1, ge=1, le=3, description="1=Question, 2=Clue, 3=Explanation")

class CoachAskRequest(BaseModel):
    challenge_id: str = Field(..., description="ID of the coding challenge")
    code: str = Field(..., description="Student's current editor code")
    question: str = Field(..., description="Student's query for the tutor")
    language: Optional[str] = Field("python", description="Language of current workspace")
    recent_error: Optional[str] = Field(None, description="Recent error string if any")

class CreateStudentRequest(BaseModel):
    display_name: Optional[str] = None


# Helper to authenticate or resolve student
def resolve_student_id(request: Optional[Request] = None, header_student_id: Optional[str] = None) -> str:
    if request:
        acc = get_optional_account(request)
        if acc and acc.get("role") == "student":
            return acc["id"]

    conn = get_db()
    cursor = conn.cursor()

    if header_student_id:
        cursor.execute("SELECT id FROM students WHERE id = ?", (header_student_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row["id"]
        # Auto-register provided pseudonymous student ID
        name = f"Coder_{random.randint(100, 999)}"
        cursor.execute("INSERT INTO students (id, display_name) VALUES (?, ?)", (header_student_id, name))
        conn.commit()
        conn.close()
        return header_student_id

    # Fallback to session user if logged in as admin/teacher testing labs
    if request:
        acc = get_optional_account(request)
        if acc:
            conn.close()
            return acc["id"]

    # Default to sample student or auto-provision
    cursor.execute("SELECT id FROM students WHERE id = 'stu_alex_vance'")
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing["id"]

    # Provision pseudonymous student
    new_id = f"stu_{uuid.uuid4().hex[:8]}"
    name = f"Coder_{random.randint(100, 999)}"
    cursor.execute("INSERT INTO students (id, display_name) VALUES (?, ?)", (new_id, name))
    conn.commit()
    conn.close()
    return new_id


# -----------------------------------------------------------------------------
# 1. Health & Runtimes Endpoint
# -----------------------------------------------------------------------------
@router.get("/health")
def health_check():
    """Returns service health only; never exposes secrets or internal paths."""
    return {
        "status": "ok",
        "service": "student-coding-quest-api",
        "version": "1.0.0"
    }


@router.get("/runtimes")
def list_runtimes():
    """Returns host compiler and runtime availability; never displays fake success."""
    return {"runtimes": get_available_runtimes()}


@router.get("/ai-status")
def ai_status():
    """Returns provider readiness and model status without exposing the API key."""
    import os
    has_key = is_ai_configured()
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    return {
        "configured": has_key,
        "ai_configured": has_key,
        "provider": "Google Gemini" if has_key else "Built-in Socratic Rules Engine",
        "model": model if has_key else "local-pedagogical-rules",
        "status_label": f"Live Gemini AI Active ({model})" if has_key else "Offline Socratic Engine Active (No GEMINI_API_KEY set)",
        "can_generate_solution": False,
        "rule": "Student must write every line. AI provides questions and conceptual hints only."
    }


# -----------------------------------------------------------------------------
# 2. Languages Catalog & Curriculum Endpoints
# -----------------------------------------------------------------------------
@router.get("/languages")
def list_languages():
    """Returns complete catalog of programming languages with real-time host toolchain status."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, skill_tag, execution_language, difficulty, xp_reward FROM challenges WHERE active = 1")
    challenges = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"languages": get_all_languages_summary(challenges)}


@router.get("/languages/{lang_id}")
def get_language(lang_id: str):
    """Returns deep-dive language page details, lessons, code examples, setup guide, and challenges."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, skill_tag, execution_language, difficulty, xp_reward, prompt, concept_recap, related_challenge_id FROM challenges WHERE active = 1")
    challenges = [dict(r) for r in cursor.fetchall()]
    conn.close()
    data = get_language_details(lang_id, challenges)
    if not data:
        raise HTTPException(status_code=404, detail=f"Language '{lang_id}' not found in catalog.")
    return data


# -----------------------------------------------------------------------------
# 3. Challenges Endpoint
# -----------------------------------------------------------------------------
@router.get("/challenges")
def list_challenges(
    skill: Optional[str] = Query(None, description="Filter by skill tag"),
    level: Optional[str] = Query(None, description="Filter by difficulty level"),
    language: Optional[str] = Query(None, description="Filter by programming language")
):
    """
    Returns active mission catalog without private test suites.
    Hidden tests remain strictly private to the server.
    """
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT id, title, skill_tag, execution_language, difficulty, prompt, starter_code, xp_reward, active, concept_recap, related_challenge_id
        FROM challenges
        WHERE active = 1
    """
    params = []
    if skill:
        query += " AND LOWER(skill_tag) = LOWER(?)"
        params.append(skill)
    if level:
        query += " AND LOWER(difficulty) = LOWER(?)"
        params.append(level)
    if language:
        lang_norm = language.lower().strip()
        aliases = {"py": "python", "sqlite": "sql", "css": "html", "web": "html", "js": "javascript", "c++": "cpp"}
        lang_norm = aliases.get(lang_norm, lang_norm)
        query += " AND LOWER(execution_language) = ?"
        params.append(lang_norm)

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    challenges = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {"challenges": challenges}


@router.get("/challenges/{challenge_id}")
def get_challenge(challenge_id: str):
    norm_id = MISSION_MAPPING.get(challenge_id, challenge_id)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, skill_tag, execution_language, difficulty, prompt, starter_code, xp_reward, active, concept_recap, related_challenge_id
        FROM challenges
        WHERE id = ? AND active = 1
    """, (norm_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Challenge not found or inactive.")
    return dict(row)


# -----------------------------------------------------------------------------
# 3. Code Submission & Attempt Runner (Isolated Sandbox)
# -----------------------------------------------------------------------------
@router.post("/attempts")
def submit_attempt(req: AttemptRequest, request: Request, x_student_id: Optional[str] = Header(None)):
    student_id = resolve_student_id(request, x_student_id)
    norm_challenge_id = MISSION_MAPPING.get(req.challenge_id, req.challenge_id)

    conn = get_db()
    cursor = conn.cursor()

    # Load challenge and private test suite
    cursor.execute("SELECT * FROM challenges WHERE id = ?", (norm_challenge_id,))
    challenge = cursor.fetchone()
    if not challenge:
        conn.close()
        raise HTTPException(status_code=404, detail="Challenge not found.")

    expected_language = (challenge["execution_language"] or "python").lower()
    supplied_language = (req.language or expected_language).lower()
    language_aliases = {"py": "python", "python3": "python", "sqlite": "sql", "sqlite3": "sql", "css": "html", "web": "html", "js": "javascript", "c++": "cpp", "cplusplus": "cpp"}
    supplied_language = language_aliases.get(supplied_language, supplied_language)

    # Check host toolchain readiness first: if runtime is absent, report gracefully with setup guide
    rt_check = check_language_runtime(supplied_language)
    if not rt_check["available"]:
        conn.close()
        test_report = execute_in_sandbox(
            challenge_id=norm_challenge_id,
            student_code=req.code,
            test_spec_json=challenge["tests"],
            language=supplied_language,
            timeout_seconds=3.0
        )
        return {
            "attempt_id": f"att_{uuid.uuid4().hex[:12]}",
            "passed": False,
            "runtime_available": False,
            "feedback": test_report.get("feedback", f"Runtime Notice: {supplied_language} compiler is not installed or not found on host PATH."),
            "error_summary": test_report.get("error_summary", f"RuntimeUnavailable: {supplied_language}"),
            "xp_earned": 0,
            "details": test_report.get("details", []),
            "progress": {
                "total_xp": 0,
                "level": 1,
                "xp_per_level": 100,
                "completed": False
            }
        }

    if supplied_language != expected_language:
        conn.close()
        raise HTTPException(status_code=422, detail=f"This lab expects {expected_language}; select that language before running it.")

    # Execute inside isolated sandbox subprocess (NEVER in API server process)
    test_report = execute_in_sandbox(
        challenge_id=norm_challenge_id,
        student_code=req.code,
        test_spec_json=challenge["tests"],
        language=req.language or "python",
        timeout_seconds=3.0
    )

    attempt_id = f"att_{uuid.uuid4().hex[:12]}"
    runtime_available = test_report.get("runtime_available", True)
    passed = 1 if (runtime_available and test_report.get("passed")) else 0
    safe_error = test_report.get("error_summary")
    xp_earned = 0

    try:
        # Atomic Transaction for attempt recording, progress, and XP ledger
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute("""
            INSERT INTO attempts (id, student_id, challenge_id, code_snapshot, passed, error_summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (attempt_id, student_id, norm_challenge_id, req.code, passed, safe_error))

        if passed == 1:
            # Check if this student already completed this challenge
            cursor.execute("""
                SELECT completed_at, xp_awarded FROM challenge_progress
                WHERE student_id = ? AND challenge_id = ?
            """, (student_id, norm_challenge_id))
            progress_row = cursor.fetchone()

            if not progress_row:
                # First time completing challenge: award XP and record progress
                xp_to_award = challenge["xp_reward"]
                xp_earned = xp_to_award

                cursor.execute("""
                    INSERT INTO challenge_progress (student_id, challenge_id, best_attempt_id, xp_awarded)
                    VALUES (?, ?, ?, ?)
                """, (student_id, norm_challenge_id, attempt_id, xp_to_award))

                ledger_id = f"xp_{uuid.uuid4().hex[:12]}"
                cursor.execute("""
                    INSERT INTO xp_ledger (id, student_id, challenge_id, amount, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (ledger_id, student_id, norm_challenge_id, xp_to_award, f"Completed challenge: {challenge['title']}"))
            else:
                # Already completed in a prior attempt: update best attempt but award 0 XP (prevents farming)
                cursor.execute("""
                    UPDATE challenge_progress SET best_attempt_id = ?
                    WHERE student_id = ? AND challenge_id = ?
                """, (attempt_id, student_id, norm_challenge_id))
                xp_earned = 0

        # Calculate current total XP and derived level
        cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_xp FROM xp_ledger WHERE student_id = ?", (student_id,))
        total_xp = cursor.fetchone()["total_xp"]
        from app.database import get_xp_per_level
        xp_per_level = get_xp_per_level()
        level = (total_xp // xp_per_level) + 1

        # Check if challenge is completed
        cursor.execute("""
            SELECT 1 FROM challenge_progress WHERE student_id = ? AND challenge_id = ?
        """, (student_id, norm_challenge_id))
        is_completed = cursor.fetchone() is not None

        conn.commit()

    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database transaction failure: {str(e)}")

    conn.close()

    return {
        "attempt_id": attempt_id,
        "passed": bool(passed),
        "runtime_available": runtime_available,
        "feedback": test_report.get("feedback", "Test completed."),
        "error_summary": safe_error,
        "xp_earned": xp_earned,
        "details": test_report.get("details", []),
        "progress": {
            "total_xp": total_xp,
            "level": level,
            "xp_per_level": xp_per_level,
            "completed": is_completed
        }
    }


# -----------------------------------------------------------------------------
# 4. Progressive Staged Hints (Question -> Clue -> Explanation)
# -----------------------------------------------------------------------------
@router.post("/hints")
def request_hint(req: HintRequest, request: Request, x_student_id: Optional[str] = Header(None)):
    student_id = resolve_student_id(request, x_student_id)
    norm_challenge_id = MISSION_MAPPING.get(req.challenge_id, req.challenge_id)

    # The AI helps students debug by giving:
    # Level 1: A guiding question first
    # Level 2: A clearer hint / clue
    # Level 3: A full explanation if needed
    hint = get_staged_hint(norm_challenge_id, req.hint_level)

    # Record hint event in database (avoids storing excessive chat text)
    conn = get_db()
    cursor = conn.cursor()
    hint_event_id = f"hint_{uuid.uuid4().hex[:12]}"
    cursor.execute("""
        INSERT INTO hint_events (id, student_id, challenge_id, hint_level, skill_tag)
        VALUES (?, ?, ?, ?, ?)
    """, (hint_event_id, student_id, norm_challenge_id, req.hint_level, hint["skill_tag"]))
    conn.commit()
    conn.close()

    return {
        "hint_event_id": hint_event_id,
        "challenge_id": req.challenge_id,
        "hint_level": req.hint_level,
        "hint_type": hint["hint_type"],
        "skill_tag": hint["skill_tag"],
        "message": hint["message"]
    }


@router.post("/coach/ask")
def ask_socratic_coach(req: CoachAskRequest, x_student_id: Optional[str] = Header(None)):
    """
    Socratic AI Coach Q&A endpoint.
    Strictly follows Core Learning Rule: Never provides complete solution code.
    Explains concepts, translates errors into plain English, and provides guiding questions.
    """
    norm_challenge_id = MISSION_MAPPING.get(req.challenge_id, req.challenge_id)
    conn = get_db()
    challenge = conn.execute(
        "SELECT title, prompt FROM challenges WHERE id = ? AND active = 1",
        (norm_challenge_id,)
    ).fetchone()
    conn.close()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found or inactive.")

    response = socratic_coach_response(
        challenge_id=norm_challenge_id,
        student_code=req.code,
        user_question=req.question,
        language=req.language or "python",
        recent_error=req.recent_error,
        problem_context=f"{challenge['title']}: {challenge['prompt']}"
    )
    return response


# -----------------------------------------------------------------------------
# 5. Student Progress & Profile
# -----------------------------------------------------------------------------
@router.get("/students/{student_id}/progress")
def get_student_progress(student_id: str, request: Request):
    acc = get_optional_account(request)
    if acc and acc.get("role") == "student" and acc["id"] != student_id:
        raise HTTPException(status_code=403, detail="Access denied. Students can only view their own progress.")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, display_name, created_at FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="Student profile not found.")

    # Calculate total XP directly from auditable ledger
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_xp FROM xp_ledger WHERE student_id = ?", (student_id,))
    total_xp = cursor.fetchone()["total_xp"]
    from app.database import get_xp_per_level
    xp_per_level = get_xp_per_level()
    level = (total_xp // xp_per_level) + 1

    # Completed challenges
    cursor.execute("""
        SELECT cp.challenge_id, cp.completed_at, cp.xp_awarded, c.title, c.skill_tag
        FROM challenge_progress cp
        JOIN challenges c ON cp.challenge_id = c.id
        WHERE cp.student_id = ?
        ORDER BY cp.completed_at DESC
    """, (student_id,))
    completed = [dict(r) for r in cursor.fetchall()]

    # Attempt counts
    cursor.execute("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_attempts
        FROM attempts
        WHERE student_id = ?
    """, (student_id,))
    attempt_stats = dict(cursor.fetchone())

    # Hint usage count
    cursor.execute("SELECT COUNT(*) as hints_requested FROM hint_events WHERE student_id = ?", (student_id,))
    hint_count = cursor.fetchone()["hints_requested"]

    conn.close()

    return {
        "student_id": student["id"],
        "display_name": student["display_name"],
        "total_xp": total_xp,
        "level": level,
        "xp_per_level": xp_per_level,
        "completed_count": len(completed),
        "completed_challenges": completed,
        "total_attempts": attempt_stats["total_attempts"] or 0,
        "passed_attempts": attempt_stats["passed_attempts"] or 0,
        "hints_requested": hint_count
    }


# Helper endpoint to provision a new anonymous student
@router.post("/students")
def create_student(req: CreateStudentRequest):
    conn = get_db()
    cursor = conn.cursor()
    new_id = f"stu_{uuid.uuid4().hex[:8]}"
    adjectives = ["Cosmic", "Pixel", "Byte", "Swift", "Apex", "Nova", "Cyber"]
    nouns = ["Coder", "Hacker", "Pioneer", "Runner", "Crafter", "Sage"]
    default_name = f"{random.choice(adjectives)}{random.choice(nouns)}_{random.randint(10, 99)}"
    display_name = req.display_name.strip() if (req.display_name and req.display_name.strip()) else default_name

    cursor.execute("INSERT INTO students (id, display_name) VALUES (?, ?)", (new_id, display_name))
    conn.commit()
    conn.close()

    return {
        "id": new_id,
        "display_name": display_name
    }
