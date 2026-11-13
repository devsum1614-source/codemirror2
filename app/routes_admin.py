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
from app.languages import (
    LANGUAGES_CATALOG,
    get_student_assigned_programs,
    normalize_program_language_id,
)
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
    identifier: Optional[str] = Field(None, description="Email, username, or account ID")
    email: Optional[str] = Field(None, description="Email address")
    password: str = Field(..., description="Account password")
    remember_me: Optional[bool] = Field(False, description="Persist session cookie across restarts")

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
    assigned_programs: Optional[List[str]] = None


class StudentProgramAssignPayload(BaseModel):
    language_id: Optional[str] = None
    language_ids: Optional[List[str]] = None
    program_id: Optional[str] = None
    programs: Optional[List[str]] = None


def _get_teacher_allowed_class_ids(conn, account: Dict[str, Any]) -> set:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM classes WHERE teacher_id = ? OR id = ?",
        (account.get("id") or "", account.get("class_id") or "")
    )
    allowed = {r["id"] for r in cursor.fetchall()}
    if account.get("class_id"):
        allowed.add(account["class_id"])
    return allowed


def _can_staff_manage_student(conn, account: Dict[str, Any], student_row: Any) -> bool:
    role = (account.get("role") or "").lower()
    if role == "owner":
        return True
    if role == "teacher":
        stu_class_id = student_row["class_id"] if isinstance(student_row, dict) else student_row["class_id"]
        if not stu_class_id:
            return True
        allowed_classes = _get_teacher_allowed_class_ids(conn, account)
        return stu_class_id in allowed_classes
    return False


def _ensure_staff_can_manage_student(conn, account: Dict[str, Any], student_row: Any) -> None:
    if not _can_staff_manage_student(conn, account, student_row):
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Access denied. Teachers may only manage students enrolled in their assigned classes."
        )

from app.auth import get_current_account, require_role, get_optional_account


# -----------------------------------------------------------------------------
# 1. Real Server-Side Auth (Password verification, sessions, student registration)
# -----------------------------------------------------------------------------
@router.post("/auth/login")
def login(payload: LoginRequest, request: Request, response: Response):
    raw_ident = payload.email or payload.identifier or ""
    ident = raw_ident.strip().lower()
    if not ident or not payload.password:
        raise HTTPException(
            status_code=401,
            detail="Unable to sign in. Please check your email and password and try again."
        )

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
        raise HTTPException(
            status_code=401,
            detail="Unable to sign in. Please check your email and password and try again."
        )

    token = create_session(account["id"], account["role"])
    cookie_kwargs = {
        "key": "cm_session",
        "value": token,
        "httponly": True,
        "samesite": "lax",
        "secure": request.url.scheme == "https"
    }
    if payload.remember_me:
        cookie_kwargs["max_age"] = 30 * 86400
    response.set_cookie(**cookie_kwargs)
    return {
        "status": "success",
        "token": token,
        "remember_me": bool(payload.remember_me),
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
        for default_lang in ("python", "sql", "html"):
            cursor.execute("""
                INSERT OR IGNORE INTO student_programs (student_id, language_id, assigned_by)
                VALUES (?, ?, 'system_default')
            """, (new_student_id, default_lang))
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
CHALLENGE_LESSON_MAP = {
    "ch_py_filter": "Python: Loops & Defensive API Filtering",
    "ch_c_bounds": "Python: Guarding Empty Lists Before Division",
    "ch_web_validator": "Python: String Trimming & Input Validation",
    "ch_py_first_steps": "Python: Reusable Functions & Return Values",
    "ch_sql_search": "SQL: INNER JOIN & Filtering Active Rows",
    "ch_algo_bsearch": "Python: Binary Search & Index Boundaries",
    "ch_java_grade_calculator": "Python: Safe Grade Average Calculation",
    "ch_html_profile_card": "HTML & CSS: Semantic Profile Markup",
}

SKILL_LESSON_MAP = {
    "python-backend": "Python: Loops & Defensive API Filtering",
    "python-basics": "Python: Functions, Lists & Boundary Guards",
    "web-validation": "Python: String Trimming & Input Validation",
    "sql-databases": "SQL: Relational Queries & Joins",
    "algorithms": "Python: Search & Boundary Conditions",
    "web-markup": "HTML & CSS: Semantic Structure",
}

SUPPLIED_SAMPLE_COMMON_ERRORS = [
    {
        "challenge_id": "ch_py_filter",
        "challenge_title": "REST API Endpoint: Category & Status Filtering",
        "skill_tag": "python-backend",
        "error_summary": "TimeoutExpired: Operation exceeded allowable execution time.",
        "frequency": 26,
    },
    {
        "challenge_id": "ch_py_filter",
        "challenge_title": "REST API Endpoint: Category & Status Filtering",
        "skill_tag": "python-backend",
        "error_summary": "invalid_status_exception: Expected ValueError but none was raised.",
        "frequency": 26,
    },
    {
        "challenge_id": "ch_c_bounds",
        "challenge_title": "Guard Empty Lists Before Averaging",
        "skill_tag": "python-basics",
        "error_summary": "RuntimeUnavailable: C toolchain not found on server host.",
        "frequency": 22,
    },
    {
        "challenge_id": "ch_c_bounds",
        "challenge_title": "Guard Empty Lists Before Averaging",
        "skill_tag": "python-basics",
        "error_summary": "empty_scores_zero_guard: Runtime error: float division by zero",
        "frequency": 9,
    },
    {
        "challenge_id": "ch_c_bounds",
        "challenge_title": "Guard Empty Lists Before Averaging",
        "skill_tag": "python-basics",
        "error_summary": "empty_scores_zero_guard: Function 'calculate_average_rating' not defined in code.",
        "frequency": 3,
    },
    {
        "challenge_id": "ch_web_validator",
        "challenge_title": "Prevent Empty & Whitespace Resource Titles",
        "skill_tag": "web-validation",
        "error_summary": "SyntaxError: invalid syntax (line 1)",
        "frequency": 1,
    },
]


def classify_error_category(error_summary: str) -> str:
    text = (error_summary or "").lower()
    if "syntaxerror" in text or "invalid syntax" in text:
        return "Syntax Error"
    if "timeout" in text or "exceeded allowable execution time" in text:
        return "Timeout"
    if "runtimeunavailable" in text or "toolchain" in text or "not installed" in text:
        return "Toolchain / Environment"
    if "division by zero" in text or "zerodivision" in text or "runtime error" in text:
        return "Runtime Error"
    if "not defined" in text or "nameerror" in text:
        return "Missing Definition"
    if "valueerror" in text or "exception" in text or "expected" in text or "assertion" in text:
        return "Validation / Exception"
    return "Logic / Test Failure"


def _enrich_error_topics(raw_rows: List[Dict[str, Any]], is_sample: bool) -> List[Dict[str, Any]]:
    enriched = []
    for idx, row in enumerate(raw_rows, start=1):
        ch_id = row.get("challenge_id") or ""
        skill = row.get("skill_tag") or "general"
        summary = row.get("error_summary") or row.get("topic") or "Test execution failure"
        freq = int(row.get("frequency") or row.get("count") or 1)
        lesson = (
            row.get("related_lesson")
            or CHALLENGE_LESSON_MAP.get(ch_id)
            or SKILL_LESSON_MAP.get(skill)
            or "Core Programming Fundamentals"
        )
        category = row.get("error_category") or classify_error_category(summary)
        enriched.append({
            "rank": idx,
            "challenge_id": ch_id,
            "challenge_title": row.get("challenge_title") or "Coding Challenge",
            "skill_tag": skill,
            "related_lesson": lesson,
            "error_category": category,
            "error_summary": summary,
            "frequency": freq,
            "count": freq,
            "is_sample_data": is_sample,
        })
    return enriched


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

    # Active learning programs & completed labs across enrolled students
    cursor.execute("""
        SELECT COUNT(*) as total_assignments, COUNT(DISTINCT language_id) as distinct_programs
        FROM student_programs sp
        JOIN accounts acc ON sp.student_id = acc.id
        WHERE acc.role = 'student'
    """)
    prog_row = cursor.fetchone()
    active_programs = int(prog_row["total_assignments"] or 0)
    distinct_programs = int(prog_row["distinct_programs"] or 0)

    cursor.execute("""
        SELECT COUNT(*) as completed_labs
        FROM challenge_progress cp
        JOIN accounts acc ON cp.student_id = acc.id
        WHERE acc.role = 'student'
    """)
    completed_labs = int(cursor.fetchone()["completed_labs"] or 0)

    # Recent student progress feed (completed labs + recent attempts)
    cursor.execute("""
        SELECT
            cp.student_id,
            COALESCE(acc.display_name, cp.student_id) as student_name,
            acc.class_id,
            COALESCE(cls.name, acc.class_id, 'Unassigned') as class_name,
            cp.challenge_id,
            c.title as challenge_title,
            c.execution_language as language_id,
            cp.xp_awarded,
            cp.completed_at as timestamp
        FROM challenge_progress cp
        LEFT JOIN accounts acc ON cp.student_id = acc.id
        LEFT JOIN classes cls ON acc.class_id = cls.id
        JOIN challenges c ON cp.challenge_id = c.id
        WHERE acc.role = 'student' OR acc.role IS NULL
        ORDER BY cp.completed_at DESC
        LIMIT 8
    """)
    recent_progress = []
    for row in cursor.fetchall():
        lang_id = (row["language_id"] or "python").lower()
        lang_meta = LANGUAGES_CATALOG.get(lang_id, {"name": lang_id.upper(), "icon": "💻"})
        recent_progress.append({
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "class_id": row["class_id"],
            "class_name": row["class_name"],
            "challenge_id": row["challenge_id"],
            "challenge_title": row["challenge_title"],
            "language_id": lang_id,
            "program_name": lang_meta["name"],
            "program_icon": lang_meta["icon"],
            "status": "Completed Lab",
            "xp_awarded": int(row["xp_awarded"] or 0),
            "timestamp": row["timestamp"],
        })

    # Program enrollment summary across catalog languages
    cursor.execute("""
        SELECT sp.language_id, COUNT(DISTINCT sp.student_id) as enrolled_count
        FROM student_programs sp
        JOIN accounts acc ON sp.student_id = acc.id
        WHERE acc.role = 'student'
        GROUP BY sp.language_id
    """)
    enrolled_by_lang = {r["language_id"]: int(r["enrolled_count"] or 0) for r in cursor.fetchall()}

    cursor.execute("""
        SELECT LOWER(c.execution_language) as lang_id, COUNT(*) as completed_count
        FROM challenge_progress cp
        JOIN challenges c ON cp.challenge_id = c.id
        JOIN accounts acc ON cp.student_id = acc.id
        WHERE acc.role = 'student'
        GROUP BY LOWER(c.execution_language)
    """)
    completed_by_lang = {r["lang_id"]: int(r["completed_count"] or 0) for r in cursor.fetchall()}

    program_summary = []
    for lang_id, meta in LANGUAGES_CATALOG.items():
        program_summary.append({
            "language_id": lang_id,
            "name": meta["name"],
            "icon": meta["icon"],
            "enrolled_students": enrolled_by_lang.get(lang_id, 0),
            "completed_labs": completed_by_lang.get(lang_id, 0),
        })

    # Aggregated sandbox test-run errors (grouped without student PII)
    cursor.execute("""
        SELECT 
            c.id as challenge_id,
            c.title as challenge_title,
            c.skill_tag,
            a.error_summary,
            COUNT(*) as frequency
        FROM attempts a
        JOIN challenges c ON a.challenge_id = c.id
        WHERE a.passed = 0 AND a.error_summary IS NOT NULL
        GROUP BY c.id, c.title, c.skill_tag, a.error_summary
        ORDER BY frequency DESC, c.title ASC
        LIMIT 12
    """)
    live_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if live_rows:
        is_sample = False
        telemetry_source = "sandbox_attempts"
        telemetry_status_label = "Aggregated Sandbox Data"
        common_errors = _enrich_error_topics(live_rows, is_sample=False)
    else:
        is_sample = True
        telemetry_source = "sample_data"
        telemetry_status_label = "Sample Data"
        common_errors = _enrich_error_topics(SUPPLIED_SAMPLE_COMMON_ERRORS, is_sample=True)

    return {
        "viewer_role": account["role"],
        "telemetry_source": telemetry_source,
        "telemetry_status_label": telemetry_status_label,
        "is_sample_data": is_sample,
        "telemetry_note": "Aggregated sandbox test-run errors for instructor review. Student identities are never exposed.",
        "metrics": {
            "total_students": total_students,
            "total_classes": total_classes,
            "total_challenges": total_challenges,
            "active_challenges": active_challenges,
            "active_programs": active_programs,
            "distinct_programs": distinct_programs,
            "completed_labs": completed_labs,
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "overall_pass_rate": pass_rate
        },
        "recent_progress": recent_progress,
        "program_summary": program_summary,
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
            student["assigned_programs"] = get_student_assigned_programs(conn, student["id"])
            student["assigned_programs_count"] = len(student["assigned_programs"])

    conn.close()
    return {"classes": classes}


@router.get("/admin/students")
def list_admin_students(
    q: Optional[str] = None,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """
    Staff (owner and teacher) can search for students across the platform,
    inspect their learning progress, assigned programs, and open their SkillProof profile.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            acc.id,
            acc.display_name,
            acc.email,
            acc.class_id,
            acc.created_at,
            cls.name as class_name,
            COALESCE((SELECT SUM(amount) FROM xp_ledger xl WHERE xl.student_id = acc.id), 0) as total_xp,
            (SELECT COUNT(*) FROM challenge_progress cp WHERE cp.student_id = acc.id) as completed_count
        FROM accounts acc
        LEFT JOIN classes cls ON acc.class_id = cls.id
        WHERE acc.role = 'student'
        ORDER BY total_xp DESC, acc.display_name ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]

    from app.database import get_xp_per_level
    xp_per_lvl = get_xp_per_level()

    students = []
    search_term = (q or "").strip().lower()
    for s in rows:
        if not _can_staff_manage_student(conn, account, s):
            continue
        s["level"] = (s["total_xp"] // xp_per_lvl) + 1
        s["skillproof_count"] = s["completed_count"]
        s["assigned_programs"] = get_student_assigned_programs(conn, s["id"])
        s["assigned_programs_count"] = len(s["assigned_programs"])
        if search_term:
            prog_names = " ".join(
                f"{p['language_id']} {p['name']}" for p in s["assigned_programs"]
            )
            haystack = " ".join([
                str(s.get("id") or ""),
                str(s.get("display_name") or ""),
                str(s.get("email") or ""),
                str(s.get("class_name") or ""),
                str(s.get("class_id") or ""),
                prog_names,
            ]).lower()
            if search_term not in haystack:
                continue
        students.append(s)

    conn.close()
    return {"students": students, "total": len(students)}


@router.get("/admin/students/{student_id}")
@router.get("/admin/students/{student_id}/profile")
def get_admin_student_profile(
    student_id: str,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """
    Returns a student's complete profile, assigned learning programs, completed labs,
    and verified SkillProof records for staff review.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            acc.id,
            acc.display_name,
            acc.email,
            acc.class_id,
            acc.created_at,
            cls.name as class_name
        FROM accounts acc
        LEFT JOIN classes cls ON acc.class_id = cls.id
        WHERE acc.id = ? AND acc.role = 'student'
    """, (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, student_row)

    student = dict(student_row)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_xp FROM xp_ledger WHERE student_id = ?", (student_id,))
    total_xp = int(cursor.fetchone()["total_xp"] or 0)

    from app.database import get_xp_per_level
    xp_per_lvl = get_xp_per_level()
    student["total_xp"] = total_xp
    student["level"] = (total_xp // xp_per_lvl) + 1

    # Assigned learning programs with status & progress
    assigned_programs = get_student_assigned_programs(conn, student_id)
    assigned_lang_ids = {p["language_id"] for p in assigned_programs}
    student["assigned_programs"] = assigned_programs
    student["assigned_programs_count"] = len(assigned_programs)

    # Available catalog programs for staff assignment selector
    cursor.execute("""
        SELECT LOWER(execution_language) as lang_id, COUNT(*) as cnt
        FROM challenges
        WHERE active = 1
        GROUP BY LOWER(execution_language)
    """)
    lab_counts_by_lang = {r["lang_id"]: int(r["cnt"] or 0) for r in cursor.fetchall()}

    available_catalog_programs = []
    for lang_id, meta in LANGUAGES_CATALOG.items():
        available_catalog_programs.append({
            "language_id": lang_id,
            "id": lang_id,
            "name": meta["name"],
            "icon": meta["icon"],
            "category": meta["category"],
            "difficulty": meta["difficulty"],
            "short_description": meta["short_description"],
            "lessons_count": len(meta.get("lessons", [])),
            "examples_count": len(meta.get("examples", [])),
            "total_labs": lab_counts_by_lang.get(lang_id, 0),
            "is_assigned": lang_id in assigned_lang_ids,
        })

    # Verified challenge completions (Completed Labs & SkillProof records)
    cursor.execute("""
        SELECT
            cp.challenge_id,
            cp.xp_awarded,
            cp.completed_at,
            c.title,
            c.skill_tag,
            c.execution_language,
            c.difficulty
        FROM challenge_progress cp
        JOIN challenges c ON cp.challenge_id = c.id
        WHERE cp.student_id = ?
        ORDER BY cp.completed_at DESC
    """, (student_id,))
    verified_challenges = []
    skill_counts: Dict[str, int] = {}
    for row in cursor.fetchall():
        item = dict(row)
        item["verification_source"] = "Automated Sandbox Test Suite"
        item["status"] = "Verified"
        verified_challenges.append(item)
        tag = item.get("skill_tag") or "general"
        skill_counts[tag] = skill_counts.get(tag, 0) + 1

    student["completed_count"] = len(verified_challenges)

    # Also include any project_missions / skill_evidence records if linked to the demo student
    legacy_evidence = []
    if student_id == "stu_alex_vance":
        cursor.execute("""
            SELECT evidence_id, skill_name, evidence_type, source_id, score, description, created_at
            FROM skill_evidence
            ORDER BY created_at DESC
        """)
        legacy_evidence = [dict(r) for r in cursor.fetchall()]

    # Earned badges based on total XP
    cursor.execute("SELECT id, title, description, icon, required_xp FROM badges WHERE required_xp <= ? ORDER BY required_xp ASC", (total_xp,))
    badges = [dict(b) for b in cursor.fetchall()]

    # Recent attempts log
    cursor.execute("""
        SELECT
            a.id as attempt_id,
            a.challenge_id,
            COALESCE(c.title, a.challenge_id) as challenge_title,
            a.passed,
            a.error_summary,
            a.created_at
        FROM attempts a
        LEFT JOIN challenges c ON a.challenge_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.created_at DESC
        LIMIT 10
    """, (student_id,))
    recent_attempts = [dict(r) for r in cursor.fetchall()]

    skill_breakdown = [
        {"skill_tag": tag, "verified_count": count}
        for tag, count in skill_counts.items()
    ]

    conn.close()
    return {
        "student": student,
        "assigned_programs": assigned_programs,
        "available_catalog_programs": available_catalog_programs,
        "completed_labs": verified_challenges,
        "skillproof_records": verified_challenges,
        "evidence_records": legacy_evidence,
        "skill_breakdown": skill_breakdown,
        "badges": badges,
        "recent_attempts": recent_attempts,
        "total_verifications": len(verified_challenges) + len(legacy_evidence)
    }


@router.put("/admin/students/{student_id}")
def update_student_profile(
    student_id: str,
    payload: StudentProfilePayload,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """Authorized staff (owner or student's class teacher) can update student details and assigned programs."""
    email = payload.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, class_id FROM accounts WHERE id = ?", (student_id,))
    current = cursor.fetchone()
    if not current or current["role"] != "student":
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, current)

    if payload.class_id:
        cursor.execute("SELECT id FROM classes WHERE id = ?", (payload.class_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=422, detail="Selected class does not exist.")
        if account["role"] == "teacher":
            allowed_classes = _get_teacher_allowed_class_ids(conn, account)
            if payload.class_id not in allowed_classes:
                conn.close()
                raise HTTPException(status_code=403, detail="Teachers may only assign students to their own classes.")

    normalized_programs: Optional[List[str]] = None
    if payload.assigned_programs is not None:
        normalized_programs = []
        for raw_lang in payload.assigned_programs:
            norm_lang = normalize_program_language_id(raw_lang)
            if not norm_lang:
                conn.close()
                raise HTTPException(status_code=422, detail=f"Unsupported language program '{raw_lang}'.")
            if norm_lang not in normalized_programs:
                normalized_programs.append(norm_lang)

    try:
        cursor.execute(
            "UPDATE accounts SET display_name = ?, email = ?, class_id = ? WHERE id = ? AND role = 'student'",
            (payload.display_name.strip(), email, payload.class_id or None, student_id)
        )
        cursor.execute("UPDATE students SET display_name = ? WHERE id = ?", (payload.display_name.strip(), student_id))
        if normalized_programs is not None:
            cursor.execute("DELETE FROM student_programs WHERE student_id = ?", (student_id,))
            for lang_id in normalized_programs:
                cursor.execute(
                    "INSERT OR IGNORE INTO student_programs (student_id, language_id, assigned_by) VALUES (?, ?, ?)",
                    (student_id, lang_id, account["id"])
                )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        if "UNIQUE" in str(exc).upper():
            conn.close()
            raise HTTPException(status_code=409, detail="That email address is already assigned to another account.")
        conn.close()
        raise

    updated_programs = get_student_assigned_programs(conn, student_id)
    conn.close()
    return {
        "status": "updated",
        "student_id": student_id,
        "assigned_programs": updated_programs
    }


@router.get("/admin/students/{student_id}/programs")
def list_student_programs_admin(
    student_id: str,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, class_id FROM accounts WHERE id = ? AND role = 'student'", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, student_row)
    programs = get_student_assigned_programs(conn, student_id)
    conn.close()
    return {"student_id": student_id, "assigned_programs": programs}


@router.post("/admin/students/{student_id}/programs")
def assign_student_program(
    student_id: str,
    payload: StudentProgramAssignPayload,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """Assigns one or more language learning programs from the catalog to a student."""
    raw_items: List[str] = []
    if payload.language_id:
        raw_items.append(payload.language_id)
    if payload.program_id:
        raw_items.append(payload.program_id)
    if payload.language_ids:
        raw_items.extend(payload.language_ids)
    if payload.programs:
        raw_items.extend(payload.programs)

    if not raw_items:
        raise HTTPException(status_code=422, detail="Please specify at least one language program to assign.")

    normalized_items: List[str] = []
    for raw in raw_items:
        norm = normalize_program_language_id(raw)
        if not norm:
            raise HTTPException(status_code=422, detail=f"Language '{raw}' is not in the Code Wizard language catalog.")
        if norm not in normalized_items:
            normalized_items.append(norm)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, class_id FROM accounts WHERE id = ? AND role = 'student'", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, student_row)

    for lang_id in normalized_items:
        cursor.execute("""
            INSERT INTO student_programs (student_id, language_id, assigned_by)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, language_id) DO UPDATE SET
                assigned_by = excluded.assigned_by,
                assigned_at = CURRENT_TIMESTAMP
        """, (student_id, lang_id, account["id"]))

    conn.commit()
    updated_programs = get_student_assigned_programs(conn, student_id)
    conn.close()
    return {
        "status": "assigned",
        "student_id": student_id,
        "assigned_language_ids": normalized_items,
        "assigned_programs": updated_programs
    }


@router.put("/admin/students/{student_id}/programs")
def set_student_programs(
    student_id: str,
    payload: StudentProgramAssignPayload,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """Replaces the full set of assigned learning programs for a student."""
    raw_items = payload.language_ids if payload.language_ids is not None else (payload.programs or [])
    if payload.language_id and payload.language_id not in raw_items:
        raw_items = list(raw_items) + [payload.language_id]

    normalized_items: List[str] = []
    for raw in raw_items:
        norm = normalize_program_language_id(raw)
        if not norm:
            raise HTTPException(status_code=422, detail=f"Language '{raw}' is not in the Code Wizard language catalog.")
        if norm not in normalized_items:
            normalized_items.append(norm)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, class_id FROM accounts WHERE id = ? AND role = 'student'", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, student_row)

    cursor.execute("DELETE FROM student_programs WHERE student_id = ?", (student_id,))
    for lang_id in normalized_items:
        cursor.execute(
            "INSERT INTO student_programs (student_id, language_id, assigned_by) VALUES (?, ?, ?)",
            (student_id, lang_id, account["id"])
        )

    conn.commit()
    updated_programs = get_student_assigned_programs(conn, student_id)
    conn.close()
    return {
        "status": "updated",
        "student_id": student_id,
        "assigned_programs": updated_programs
    }


@router.delete("/admin/students/{student_id}/programs/{language_id}")
def remove_student_program(
    student_id: str,
    language_id: str,
    account: Dict[str, Any] = Depends(require_role(["owner", "teacher"]))
):
    """Removes a learning program assignment from a student."""
    norm_lang = normalize_program_language_id(language_id)
    if not norm_lang:
        raise HTTPException(status_code=422, detail=f"Language '{language_id}' is not in the Code Wizard language catalog.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, class_id FROM accounts WHERE id = ? AND role = 'student'", (student_id,))
    student_row = cursor.fetchone()
    if not student_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student account not found.")

    _ensure_staff_can_manage_student(conn, account, student_row)

    cursor.execute(
        "DELETE FROM student_programs WHERE student_id = ? AND language_id = ?",
        (student_id, norm_lang)
    )
    conn.commit()
    updated_programs = get_student_assigned_programs(conn, student_id)
    conn.close()
    return {
        "status": "removed",
        "student_id": student_id,
        "removed_language_id": norm_lang,
        "assigned_programs": updated_programs
    }


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
