import sqlite3
import os
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "codemirror.db"

def get_xp_per_level(default: int = 100) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT value FROM site_settings WHERE key IN ('xp_multiplier_per_level', 'xp_per_level') "
        "ORDER BY CASE key WHEN 'xp_multiplier_per_level' THEN 0 ELSE 1 END LIMIT 1"
    ).fetchone()
    conn.close()
    try:
        return max(1, int(row["value"])) if row else default
    except (TypeError, ValueError):
        return default

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    -- =========================================================================
    -- ACCOUNTS, ROLES & CLASSROOMS (Role-based access: student, teacher, owner)
    -- =========================================================================

    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', -- 'student', 'teacher', 'owner'
        password_hash TEXT,
        class_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions(account_id);

    CREATE TABLE IF NOT EXISTS classes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        teacher_id TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES accounts(id)
    );

    CREATE TABLE IF NOT EXISTS site_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS badges (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        required_xp INTEGER DEFAULT 0
    );

    -- =========================================================================
    -- STUDENT CODING QUEST SPECIFICATION TABLES
    -- =========================================================================

    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS challenges (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        skill_tag TEXT NOT NULL,
        execution_language TEXT NOT NULL DEFAULT 'python',
        difficulty TEXT NOT NULL,
        prompt TEXT NOT NULL,
        starter_code TEXT NOT NULL,
        tests TEXT NOT NULL, -- private test cases (JSON/text), never sent to student
        xp_reward INTEGER NOT NULL DEFAULT 50,
        active INTEGER NOT NULL DEFAULT 1,
        concept_recap TEXT,
        related_challenge_id TEXT
    );

    CREATE TABLE IF NOT EXISTS attempts (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        challenge_id TEXT NOT NULL,
        code_snapshot TEXT NOT NULL,
        passed INTEGER NOT NULL, -- 1 for passed, 0 for failed
        error_summary TEXT,      -- sanitized error message
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    );

    CREATE TABLE IF NOT EXISTS hint_events (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        challenge_id TEXT NOT NULL,
        hint_level INTEGER NOT NULL, -- 1=question, 2=clue, 3=explanation
        skill_tag TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    );

    CREATE TABLE IF NOT EXISTS challenge_progress (
        student_id TEXT NOT NULL,
        challenge_id TEXT NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        best_attempt_id TEXT,
        xp_awarded INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (student_id, challenge_id),
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id),
        FOREIGN KEY (best_attempt_id) REFERENCES attempts(id)
    );

    CREATE TABLE IF NOT EXISTS xp_ledger (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        challenge_id TEXT NOT NULL,
        amount INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (challenge_id) REFERENCES challenges(id)
    );

    CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);
    CREATE INDEX IF NOT EXISTS idx_hint_events_student ON hint_events(student_id);
    CREATE INDEX IF NOT EXISTS idx_xp_ledger_student ON xp_ledger(student_id);

    -- =========================================================================
    -- LEGACY / COMPATIBILITY TABLES
    -- =========================================================================

    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        language_set TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS missions (
        mission_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        track TEXT NOT NULL,
        language TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        scenario TEXT NOT NULL,
        starter_code TEXT NOT NULL,
        file_path TEXT NOT NULL,
        acceptance_criteria TEXT NOT NULL,
        impact_summary TEXT,
        solution_code TEXT,
        rubric_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS project_missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        mission_id TEXT,
        status TEXT DEFAULT 'not_started',
        score REAL DEFAULT 0,
        student_code TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        explanation TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(project_id),
        FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
    );

    CREATE TABLE IF NOT EXISTS test_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_mission_id INTEGER,
        passed_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_mission_id) REFERENCES project_missions(id)
    );

    CREATE TABLE IF NOT EXISTS test_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        test_name TEXT NOT NULL,
        status TEXT NOT NULL,
        short_message TEXT NOT NULL,
        error_detail TEXT,
        FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
    );

    CREATE TABLE IF NOT EXISTS skill_evidence (
        evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        skill_name TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        source_id TEXT,
        score REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS hint_history (
        hint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_mission_id INTEGER,
        hint_level INTEGER NOT NULL,
        topic TEXT NOT NULL,
        hint_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_mission_id) REFERENCES project_missions(id)
    );
    """)

    # Alter table migration checks if columns don't exist yet
    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN password_hash TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE challenges ADD COLUMN concept_recap TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE challenges ADD COLUMN related_challenge_id TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE challenges ADD COLUMN execution_language TEXT NOT NULL DEFAULT 'python'")
    except Exception:
        pass

    # Helper for default passwords (PBKDF2-HMAC-SHA256)
    def _default_hash(pwd: str) -> str:
        import secrets, hashlib
        salt = secrets.token_hex(16)
        k = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return f"{salt}${k.hex()}"

    # Seed default accounts (Owner, Teacher, Students) with real passwords
    default_accounts = [
        ("own_master_admin", "Site Owner (Admin)", "owner@codemirror.local", "owner", _default_hash("Admin@Pass2026!"), None),
        ("tea_alan_turing", "Prof. Alan Turing", "turing@campus.edu", "teacher", _default_hash("Teacher@Pass2026!"), "cls_cs101"),
        ("stu_alex_vance", "PixelPioneer (Alex)", "alex.vance@campus.edu", "student", _default_hash("Student@Pass2026!"), "cls_cs101"),
        ("stu_maya_lin", "ByteVoyager (Maya)", "maya.lin@campus.edu", "student", _default_hash("Student@Pass2026!"), "cls_cs101"),
        ("stu_kai_chen", "NovaCoder (Kai)", "kai.chen@campus.edu", "student", _default_hash("Student@Pass2026!"), "cls_web200")
    ]
    for acc in default_accounts:
        cursor.execute("""
            INSERT INTO accounts (id, display_name, email, role, password_hash, class_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                display_name=excluded.display_name,
                email=excluded.email,
                role=excluded.role,
                password_hash=COALESCE(accounts.password_hash, excluded.password_hash),
                class_id=excluded.class_id
        """, acc)

    # Ensure any existing accounts with NULL password_hash get a working default password
    cursor.execute("UPDATE accounts SET password_hash = ? WHERE password_hash IS NULL AND role = 'owner'", (_default_hash("Admin@Pass2026!"),))
    cursor.execute("UPDATE accounts SET password_hash = ? WHERE password_hash IS NULL AND role = 'teacher'", (_default_hash("Teacher@Pass2026!"),))
    cursor.execute("UPDATE accounts SET password_hash = ? WHERE password_hash IS NULL AND role = 'student'", (_default_hash("Student@Pass2026!"),))

    # Seed default classes
    default_classes = [
        ("cls_cs101", "CS101: Systems & Core Algorithms", "tea_alan_turing", "Foundations of programming, memory models, algorithms, and validation."),
        ("cls_web200", "WEB200: Full-Stack Engineering & Databases", "tea_alan_turing", "Modern web services, relational SQL schemas, and FastAPI backends.")
    ]
    for cls in default_classes:
        cursor.execute("""
            INSERT INTO classes (id, name, teacher_id, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                teacher_id=excluded.teacher_id,
                description=excluded.description
        """, cls)

    # Seed default site settings
    default_settings = [
        ("xp_per_level", "100"),
        ("platform_name", "CodeMirror 2.0 - Beginner Coding Tutor"),
        ("theme_primary", "#4F46E5"),
        ("theme_background", "#F7F8FC"),
        ("theme_surface", "#FFFFFF"),
        ("theme_text", "#1B2230"),
        ("ai_guidance_tone", "Socratic, encouraging, progressive hint stages"),
        ("allow_student_signup", "true"),
        ("data_retention_days", "90"),
        ("sandbox_timeout_seconds", "3.0")
    ]
    for s in default_settings:
        cursor.execute("""
            INSERT INTO site_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, s)

    # Seed default badges
    default_badges = [
        ("badge_first_solve", "First Bug Squashed", "Completed your very first coding mission.", "🐞", 50),
        ("badge_sql_master", "SQL Query Sleuth", "Joined relational tables and optimized queries.", "🗄️", 75),
        ("badge_api_architect", "API Architect", "Engineered validated backend REST endpoints.", "⚡", 150),
        ("badge_algo_expert", "Algorithm Specialist", "Implemented logarithmic O(log N) binary search.", "📈", 200)
    ]
    for b in default_badges:
        cursor.execute("""
            INSERT INTO badges (id, title, description, icon, required_xp)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                icon=excluded.icon,
                required_xp=excluded.required_xp
        """, b)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
