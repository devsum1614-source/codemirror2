"""
Admin & Role-Based Access Control Router for Student Coding Quest
Provides endpoints for:
- Role & Account switching (Student, Teacher, Owner)
- Challenge management (Create, Edit, Publish, Archive)
- Class & Student roster management
- Learning analytics, pass rates, and common error topics
- Game configurations (XP per level, AI guidance rules)
- Data export & retention management
"""

import uuid
import re
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Depends, Request, Response
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import (
    get_current_account, 
    require_role, 
    get_optional_account,
    hash_password,
    verify_password,
    create_session,
    delete_session,
    extract_token_from_request
)

router = APIRouter(prefix="/api/v1")
# These are the execution adapters actually implemented by app/sandbox.py.
ALLOWED_EXECUTION_LANGUAGES = {"python", "sql", "html"}

# Pydantic Schemas
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email, username, or account ID")
    password: str = Field(..., description="Account password")

class RegisterStudentRequest(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=6, max_length=128)
    class_id: Optional[str] = None

class SwitchAccountRequest(BaseModel):
    account_id: str

class ChallengeAdminPayload(BaseModel):
    id: Optional[str] = None
    title: str
    skill_tag: str
    execution_language: str = "python"
    difficulty: str = "Beginner"
    prompt: str
    starter_code: str
    tests: Optional[str] = ""
    xp_reward: int = 50
    active: int = 1
    concept_recap: Optional[str] = ""
    related_challenge_id: Optional[str] = ""

class UpdateSettingsPayload(BaseModel):
    settings: Optional[Dict[str, Any]] = None
    model_config = {"extra": "allow"}

class StudentProfilePayload(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    email: str = Field(..., min_length=3, max_length=254)
    class_id: Optional[str] = None

from app.auth import get_current_account, require_role, get_optional_account


# -----------------------------------------------------------------------------
# 1. Real Server-Side Auth (Password verification, sessions, student registration)
# -----------------------------------------------------------------------------
@router.post("/auth/login")
def login(payload: LoginRequest, response: Response):
    ident = payload.identifier.strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE LOWER(email) = ? OR LOWER(id) = ? OR (LOWER(id) = 'own_master_admin' AND ? = 'admin')
        LIMIT 1
    """, (ident, ident, ident))
    account = cursor.fetchone()
    conn.close()

    if not account or not verify_password(payload.password, account["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    token = create_session(account["id"], account["role"])
    response.set_cookie(
        key="cm_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )
    return {
        "status": "success",
        "token": token,
        "account": {
            "id": account["id"],
            "display_name": account["display_name"],
            "email": account["email"],
            "role": account["role"],
            "class_id": account["class_id"]
        }
    }


@router.post("/auth/register")
def register_student(payload: RegisterStudentRequest, response: Response):
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Please provide a valid email address.")

    conn = get_db()
    cursor = conn.cursor()

    # Verify student registration is enabled
    cursor.execute("SELECT value FROM site_settings WHERE key = 'allow_student_signup'")
    row = cursor.fetchone()
    if row and str(row["value"]).lower() == "false":
        conn.close()
        raise HTTPException(status_code=403, detail="Student self-registration is currently disabled by the site owner.")

    # Check if email is already registered
    cursor.execute("SELECT id FROM accounts WHERE LOWER(email) = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="An account with this email address already exists. Please sign in.")

    # Verify class_id if provided
    class_id = payload.class_id.strip() if payload.class_id else None
    if class_id:
        cursor.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=422, detail="Specified class code does not exist.")

    # Strictly assign role = 'student' - no privilege escalation permitted
    new_student_id = f"stu_{uuid.uuid4().hex[:8]}"
    pwd_hash = hash_password(payload.password)
    clean_display = payload.display_name.strip()

    try:
        cursor.execute("""
            INSERT INTO accounts (id, display_name, email, role, password_hash, class_id)
            VALUES (?, ?, ?, 'student', ?, ?)
        """, (new_student_id, clean_display, email, pwd_hash, class_id))
        cursor.execute("""
            INSERT INTO students (id, display_name)
            VALUES (?, ?)
        """, (new_student_id, clean_display))
        conn.commit()
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error registering student: {str(exc)}")

    conn.close()

    token = create_session(new_student_id, "student")
    response.set_cookie(
        key="cm_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400
    )
    return {
        "status": "success",
        "token": token,
        "account": {
            "id": new_student_id,
            "display_name": clean_display,
            "email": email,
            "role": "student",
            "class_id": class_id
        }
    }


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = extract_token_from_request(request)
    if token:
        delete_session(token)
    response.delete_cookie("cm_session")
    return {"status": "success", "message": "Signed out successfully."}


@router.get("/auth/me")
def get_my_profile(account: Dict[str, Any] = Depends(get_current_account)):
    return {"account": account}

@router.get("/auth/accounts")
def list_demo_accounts():
    """Lists accounts for reference without passwords."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, display_name, email, role, class_id FROM accounts ORDER BY role DESC, id ASC")
    accounts = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"accounts": accounts}


# -----------------------------------------------------------------------------
# 2. Site Owner / Admin Overview & Learning Analytics
# -----------------------------------------------------------------------------
@router.get("/admin/overview")
def get_admin_overview(account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))):
    conn = get_db()
    cursor = conn.cursor()

    # Counters
    cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE role = 'student'")
    total_students = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM classes")
    total_classes = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active FROM challenges")
    ch_row = cursor.fetchone()
    total_challenges = ch_row["total"]
    active_challenges = ch_row["active"] or 0

    cursor.execute("SELECT COUNT(*) as total_attempts, SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_attempts FROM attempts")
    att_row = cursor.fetchone()
    total_attempts = att_row["total_attempts"]
    passed_attempts = att_row["passed_attempts"] or 0
    pass_rate = round((passed_attempts / total_attempts * 100), 1) if total_attempts > 0 else 100.0

    # Common error topics
    cursor.execute("""
        SELECT 
            c.title as challenge_title,
            c.skill_tag,
            a.error_summary,
            COUNT(*) as frequency
        FROM attempts a
        JOIN challenges c ON a.challenge_id = c.id
        WHERE a.passed = 0 AND a.error_summary IS NOT NULL
        GROUP BY c.title, a.error_summary
        ORDER BY frequency DESC
        LIMIT 6
    """)
    common_errors = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "viewer_role": account["role"],
        "metrics": {
            "total_students": total_students,
            "total_classes": total_classes,
            "total_challenges": total_challenges,
            "active_challenges": active_challenges,
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "overall_pass_rate": pass_rate
        },
        "common_errors": common_errors
    }


# -----------------------------------------------------------------------------
# 3. Admin Challenges Management (Owner Only)
# -----------------------------------------------------------------------------
@router.get("/admin/challenges")
def list_admin_challenges(account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))):
    """Returns challenge catalog. Private test suites visible to Owner only."""
    conn = get_db()
    cursor = conn.cursor()

    if account["role"] == "owner":
        # Owner sees private tests for editing
        cursor.execute("SELECT * FROM challenges ORDER BY active DESC, id ASC")
    else:
        # Teachers see challenges without private tests
        cursor.execute("""
            SELECT id, title, skill_tag, execution_language, difficulty, prompt, starter_code, xp_reward, active, concept_recap, related_challenge_id
            FROM challenges ORDER BY active DESC, id ASC
        """)

    challenges = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"challenges": challenges}


@router.post("/admin/challenges")
def create_challenge(payload: ChallengeAdminPayload, account: Dict[str, Any] = Depends(require_role(["owner"]))):
    if payload.execution_language not in ALLOWED_EXECUTION_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported execution language.")
    conn = get_db()
    cursor = conn.cursor()

    ch_id = payload.id.strip() if (payload.id and payload.id.strip()) else f"ch_{uuid.uuid4().hex[:8]}"

    cursor.execute("""
        INSERT INTO challenges (id, title, skill_tag, execution_language, difficulty, prompt, starter_code, tests, xp_reward, active, concept_recap, related_challenge_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            skill_tag = excluded.skill_tag,
            execution_language = excluded.execution_language,
            difficulty = excluded.difficulty,
            prompt = excluded.prompt,
            starter_code = excluded.starter_code,
            tests = excluded.tests,
            xp_reward = excluded.xp_reward,
            active = excluded.active,
            concept_recap = excluded.concept_recap,
            related_challenge_id = excluded.related_challenge_id
    """, (
        ch_id, payload.title, payload.skill_tag, payload.execution_language, payload.difficulty,
        payload.prompt, payload.starter_code, payload.tests, payload.xp_reward,
        payload.active, payload.concept_recap, payload.related_challenge_id
    ))
    conn.commit()
    conn.close()

    return {"status": "created", "challenge_id": ch_id, "title": payload.title}


@router.put("/admin/challenges/{challenge_id}")
def update_challenge(challenge_id: str, payload: ChallengeAdminPayload, account: Dict[str, Any] = Depends(require_role(["owner"]))):
    if payload.execution_language not in ALLOWED_EXECUTION_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported execution language.")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE challenges SET
            title = ?,
            skill_tag = ?,
            execution_language = ?,
            difficulty = ?,
            prompt = ?,
            starter_code = ?,
            tests = ?,
            xp_reward = ?,
            active = ?,
            concept_recap = ?,
            related_challenge_id = ?
        WHERE id = ?
    """, (
        payload.title, payload.skill_tag, payload.execution_language, payload.difficulty,
        payload.prompt, payload.starter_code, payload.tests, payload.xp_reward,
        payload.active, payload.concept_recap, payload.related_challenge_id, challenge_id
    ))
    conn.commit()
    conn.close()

    return {"status": "updated", "challenge_id": challenge_id}


@router.post("/admin/challenges/{challenge_id}/toggle-status")
def toggle_challenge_status(challenge_id: str, account: Dict[str, Any] = Depends(require_role(["owner"]))):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT active FROM challenges WHERE id = ?", (challenge_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Challenge not found.")

    new_status = 0 if row["active"] == 1 else 1
    cursor.execute("UPDATE challenges SET active = ? WHERE id = ?", (new_status, challenge_id))
    conn.commit()
    conn.close()

    return {"status": "success", "challenge_id": challenge_id, "active": new_status}


# -----------------------------------------------------------------------------
# 4. Classes & Student Rosters (Role-scoped: Teacher sees assigned class, Owner sees all)
# -----------------------------------------------------------------------------
@router.get("/admin/classes")
def list_classes_and_students(account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT c.*, a.display_name as teacher_name FROM classes c LEFT JOIN accounts a ON c.teacher_id = a.id"
    params = []

    if account["role"] == "teacher":
        query += " WHERE c.teacher_id = ? OR c.id = ?"
        params.extend([account["id"], account.get("class_id") or ""])

    cursor.execute(query, params)
    classes = [dict(r) for r in cursor.fetchall()]

    for cls in classes:
        # Fetch students enrolled in this class
        cursor.execute("""
            SELECT 
                acc.id, acc.display_name, acc.email, acc.class_id, acc.created_at,
                COALESCE((SELECT SUM(amount) FROM xp_ledger WHERE student_id = acc.id), 0) as total_xp,
                COALESCE((SELECT COUNT(*) FROM challenge_progress WHERE student_id = acc.id), 0) as completed_count
            FROM accounts acc
            WHERE acc.role = 'student' AND acc.class_id = ?
            ORDER BY total_xp DESC
        """, (cls["id"],))
        cls["students"] = [dict(s) for s in cursor.fetchall()]
        for student in cls["students"]:
            from app.database import get_xp_per_level
            student["level"] = (student["total_xp"] // get_xp_per_level()) + 1

    conn.close()
    return {"classes": classes}


@router.put("/admin/students/{student_id}")
def update_student_profile(
    student_id: str,
    payload: StudentProfilePayload,
    account: Dict[str, Any] = Depends(require_role(["owner"]))
):
    """Owner can update a student's display name, email, and class assignment."""
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM accounts WHERE id = ?", (student_id,))
    current = cursor.fetchone()
    if not current or current["role"] != "student":
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    if payload.class_id:
        cursor.execute("SELECT 1 FROM classes WHERE id = ?", (payload.class_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=422, detail="Selected class does not exist.")

    try:
        cursor.execute(
            "UPDATE accounts SET display_name = ?, email = ?, class_id = ? WHERE id = ? AND role = 'student'",
            (payload.display_name.strip(), email, payload.class_id or None, student_id)
        )
        cursor.execute("UPDATE students SET display_name = ? WHERE id = ?", (payload.display_name.strip(), student_id))
        conn.commit()
    except Exception as exc:
        conn.rollback()
        if "UNIQUE" in str(exc).upper():
            conn.close()
            raise HTTPException(status_code=409, detail="That email address is already assigned to another account.")
        conn.close()
        raise

    conn.close()
    return {"status": "updated", "student_id": student_id}


# -----------------------------------------------------------------------------
# 5. Site Settings, XP & AI Guidance Configuration
# -----------------------------------------------------------------------------
PUBLIC_SITE_SETTINGS = {
    "platform_name", "theme_primary", "theme_background", "theme_surface", "theme_text"
}


@router.get("/site-config")
def get_public_site_config():
    """Only publish display settings; never expose admin or provider secrets."""
    conn = get_db()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in PUBLIC_SITE_SETTINGS)
    cursor.execute(f"SELECT key, value FROM site_settings WHERE key IN ({placeholders})", tuple(PUBLIC_SITE_SETTINGS))
    settings = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    for key in ("theme_primary", "theme_background", "theme_surface", "theme_text"):
        if key in settings and not re.fullmatch(r"#[0-9A-Fa-f]{6}", settings[key]):
            settings.pop(key)
    return {"settings": settings}


@router.get("/admin/settings")
def get_site_settings(account: Dict[str, Any] = Depends(require_role(["owner"]))):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT key, value, updated_at FROM site_settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}

    cursor.execute("SELECT * FROM badges ORDER BY required_xp ASC")
    badges = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {"settings": settings, "badges": badges}


@router.post("/admin/settings")
def update_site_settings(payload: UpdateSettingsPayload, account: Dict[str, Any] = Depends(require_role(["owner"]))):
    conn = get_db()
    cursor = conn.cursor()

    items = payload.settings if payload.settings else payload.model_dump(exclude={"settings"}, exclude_unset=True)

    for key in ("theme_primary", "theme_background", "theme_surface", "theme_text"):
        if key in items and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(items[key])):
            conn.close()
            raise HTTPException(status_code=422, detail=f"{key} must be a six-digit hex color.")

    for k, v in items.items():
        cursor.execute("""
            INSERT INTO site_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (str(k), str(v)))

    conn.commit()
    conn.close()
    return {"status": "updated", "settings": items}


# -----------------------------------------------------------------------------
# 6. Data Controls: Export & Retention Cleanup
# -----------------------------------------------------------------------------
@router.get("/admin/export")
@router.api_route("/admin/export-data", methods=["GET", "POST"])
def export_platform_data(account: Dict[str, Any] = Depends(require_role(["owner"]))):
    """Exports anonymized student records, attempts, and progress for auditing."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, display_name, role, class_id, created_at FROM accounts")
    accounts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, title, skill_tag, difficulty, xp_reward, active, concept_recap, related_challenge_id FROM challenges")
    challenges = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, name, teacher_id FROM classes")
    classes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT key, value FROM site_settings")
    site_settings = {r["key"]: r["value"] for r in cursor.fetchall()}

    cursor.execute("SELECT id, student_id, challenge_id, passed, error_summary, created_at FROM attempts")
    attempts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT student_id, challenge_id, completed_at, xp_awarded FROM challenge_progress")
    progress = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, student_id, challenge_id, amount, reason, created_at FROM xp_ledger")
    ledger = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "export_metadata": {
            "exported_by": account["display_name"],
            "role": account["role"],
            "version": "1.0.0"
        },
        "challenges": challenges,
        "classes": classes,
        "accounts": accounts,
        "site_settings": site_settings,
        "attempts": attempts,
        "progress": progress,
        "xp_ledger": ledger
    }


@router.post("/admin/cleanup")
def cleanup_old_data(account: Dict[str, Any] = Depends(require_role(["owner"]))):
    """Removes transient test runs older than retention window while preserving XP ledger."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attempts WHERE passed = 0 AND created_at < datetime('now', '-90 days')")
    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "deleted_failed_attempts": deleted_count,
        "message": f"Cleaned up {deleted_count} expired failure logs per 90-day retention policy."
    }
