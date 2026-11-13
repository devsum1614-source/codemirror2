import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_unauthenticated_requests_rejected_without_session():
    # Attempting to access admin without session token must fail with 401
    resp = client.get("/api/v1/admin/overview")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]

    # Spoofing an editable X-Account-Id header without a real session token MUST fail with 401
    spoof_resp = client.get("/api/v1/admin/overview", headers={"X-Account-Id": "own_master_admin"})
    assert spoof_resp.status_code == 401
    assert "Authentication required" in spoof_resp.json()["detail"]

def test_student_forbidden_from_admin_overview():
    # Real login as student stu_alex_vance
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "alex.vance@campus.edu",
        "password": "Student@Pass2026!"
    })
    assert login_resp.status_code == 200
    student_token = login_resp.json()["token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Student accessing admin overview must be strictly forbidden (403)
    resp = client.get("/api/v1/admin/overview", headers=student_headers)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

def test_student_registration_restricted_to_student_role():
    import uuid
    random_email = f"learner_{uuid.uuid4().hex[:6]}@campus.edu"
    
    # 1. Register student
    reg_resp = client.post("/api/v1/auth/register", json={
        "display_name": "Grace Hopper",
        "email": random_email,
        "password": "GraceHopperPass2026!",
        "class_id": "cls_cs101"
    })
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["account"]["role"] == "student"
    assert "token" in reg_data

    # 2. Duplicate registration with same email should return 409 Conflict
    dup_resp = client.post("/api/v1/auth/register", json={
        "display_name": "Grace Duplicate",
        "email": random_email,
        "password": "AnotherPassword123!"
    })
    assert dup_resp.status_code == 409

    # 3. Wrong password fails with 401
    wrong_login = client.post("/api/v1/auth/login", json={
        "identifier": random_email,
        "password": "IncorrectPassword!"
    })
    assert wrong_login.status_code == 401

def test_teacher_can_view_classes_and_overview():
    # Login as teacher tea_alan_turing
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "turing@campus.edu",
        "password": "Teacher@Pass2026!"
    })
    assert login_resp.status_code == 200
    teacher_token = login_resp.json()["token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Teacher viewing admin overview
    resp = client.get("/api/v1/admin/overview", headers=teacher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert "total_students" in data["metrics"]
    assert "overall_pass_rate" in data["metrics"]

    # Teacher viewing classes
    classes_resp = client.get("/api/v1/admin/classes", headers=teacher_headers)
    assert classes_resp.status_code == 200
    classes_data = classes_resp.json()["classes"]
    assert len(classes_data) >= 1
    # Check that privacy is preserved: no passwords or hashes in student records
    for cls in classes_data:
        for s in cls["students"]:
            assert "password" not in s
            assert "password_hash" not in s

def test_teacher_forbidden_from_owner_settings():
    # Login as teacher
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "turing@campus.edu",
        "password": "Teacher@Pass2026!"
    })
    teacher_token = login_resp.json()["token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Teacher attempting to update site settings must be rejected (403)
    resp = client.post("/api/v1/admin/settings", 
                       headers=teacher_headers,
                       json={"platform_name": "Hacked Name"})
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

def test_owner_full_admin_lifecycle():
    # Login as owner
    login_resp = client.post("/api/v1/auth/login", json={
        "identifier": "owner@codemirror.local",
        "password": "Admin@Pass2026!"
    })
    assert login_resp.status_code == 200
    owner_token = login_resp.json()["token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Overview
    overview = client.get("/api/v1/admin/overview", headers=owner_headers)
    assert overview.status_code == 200

    # 2. List all challenges
    ch_list = client.get("/api/v1/admin/challenges", headers=owner_headers)
    assert ch_list.status_code == 200
    assert len(ch_list.json()["challenges"]) >= 5

    # 3. Create a new challenge
    test_ch_id = "ch_py_admin_test_unit"
    new_ch = {
        "id": test_ch_id,
        "title": "Unit Test Matrix Filter",
        "skill_tag": "python-backend",
        "difficulty": "Intermediate",
        "xp_reward": 90,
        "prompt": "Filter matrix rows by sum criteria.",
        "concept_recap": "List comprehension and matrix transformation in Python.",
        "related_challenge_id": "ch_py_filter",
        "starter_code": "def filter_matrix(matrix, threshold):\n    pass",
        "tests": "def test_filter(): pass"
    }
    create_resp = client.post("/api/v1/admin/challenges", headers=owner_headers, json=new_ch)
    assert create_resp.status_code == 200
    assert create_resp.json()["status"] == "created"

    # 4. Toggle active status (archive)
    toggle_resp = client.post(f"/api/v1/admin/challenges/{test_ch_id}/toggle-status", headers=owner_headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["active"] == 0

    # 5. Reactivate
    toggle_resp2 = client.post(f"/api/v1/admin/challenges/{test_ch_id}/toggle-status", headers=owner_headers)
    assert toggle_resp2.status_code == 200
    assert toggle_resp2.json()["active"] == 1

    # 6. Update platform settings
    settings_resp = client.post("/api/v1/admin/settings", 
                                headers=owner_headers,
                                json={"platform_name": "CodeMirror 2.0 - Verified Quest", "xp_multiplier_per_level": "350"})
    assert settings_resp.status_code == 200
    assert settings_resp.json()["status"] == "updated"

    # 7. Export platform data
    export_resp = client.get("/api/v1/admin/export", headers=owner_headers)
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "challenges" in export_data
    assert "classes" in export_data
    assert "accounts" in export_data
    assert "site_settings" in export_data


def test_login_interface_accessibility_and_security():
    # 1. Verify index.html has accessible login controls and zero hard-coded credentials
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    html = html_resp.text

    # Required accessible controls & links (Student & Staff Sign-In)
    assert 'id="student-login-identifier"' in html
    assert 'type="email"' in html
    assert 'id="student-login-password"' in html
    assert 'id="toggle-login-password"' in html
    assert 'id="login-remember-me"' in html
    assert 'id="forgot-password-link"' in html
    assert 'id="btn-submit-student-login"' in html
    assert 'id="create-account-link"' in html
    assert 'id="terms-of-service-link"' in html
    assert 'id="privacy-policy-link"' in html
    assert 'action="/api/v1/auth/login"' in html

    # Staff sign-in form controls
    assert 'id="form-admin-login"' in html
    assert 'id="admin-login-identifier"' in html
    assert 'id="admin-login-password"' in html
    assert 'id="toggle-admin-password"' in html
    assert 'id="admin-remember-me"' in html
    assert 'id="btn-submit-admin-login"' in html
    assert 'id="admin-email-error"' in html
    assert 'id="admin-password-error"' in html
    assert 'id="admin-auth-alert"' in html
    assert 'id="link-to-student-login"' in html

    admin_page_resp = client.get("/admin/login")
    assert admin_page_resp.status_code == 200

    # Must not prefill or hard-code passwords in HTML
    assert "Student@Pass2026!" not in html
    assert "Admin@Pass2026!" not in html
    assert "Teacher@Pass2026!" not in html

    # 2. Verify privacy-preserving error messages (same message for unknown email vs wrong password)
    unknown_resp = client.post("/api/v1/auth/login", json={
        "email": "nonexistent.user@campus.edu",
        "password": "SomePassword123!"
    })
    wrong_pwd_resp = client.post("/api/v1/auth/login", json={
        "email": "alex.vance@campus.edu",
        "password": "WrongPassword123!"
    })
    assert unknown_resp.status_code == 401
    assert wrong_pwd_resp.status_code == 401
    assert unknown_resp.json()["detail"] == wrong_pwd_resp.json()["detail"]

    # 3. Verify email + remember_me login works with same-origin endpoint
    remember_resp = client.post("/api/v1/auth/login", json={
        "email": "alex.vance@campus.edu",
        "password": "Student@Pass2026!",
        "remember_me": True
    })
    assert remember_resp.status_code == 200
    assert remember_resp.json()["remember_me"] is True
    assert "cm_session" in remember_resp.cookies


def test_simplified_workspace_interface():
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    html = html_resp.text

    # Architecture Impact and Project Explorer — CAMPUS PORTAL removed
    assert "Architecture Impact" not in html
    assert "id=\"impact-summary-text\"" not in html
    assert "Project Explorer" not in html
    assert "CAMPUS PORTAL" not in html

    # Simple "Files" heading and exercise-specific file list
    assert "<span>Files</span>" in html
    assert 'id="workspace-file-list"' in html
    assert "GradeAverage.java" not in html
    assert "profile_card.html" not in html

    # Core workspace buttons with plain labels
    assert 'id="run-tests-btn"' in html
    assert "Run Tests" in html
    assert 'id="save-code-btn"' in html
    assert 'id="reset-code-btn"' in html
    assert 'id="help-guide-btn"' in html

    # Workspace AI UI removed while backend AI endpoints stay intact for future restoration
    assert 'data-tab="coach"' not in html
    assert 'id="tab-pane-coach"' not in html
    assert 'id="coach-service-status"' not in html
    ai_status_resp = client.get("/api/v1/ai-status")
    assert ai_status_resp.status_code == 200


def test_code_examples_library_and_language_runners():
    # 1. Inspect the Code Examples catalog across all 7 languages
    resp = client.get("/api/v1/examples")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total_languages"] == 7
    assert payload["total_examples"] == 42

    lang_ids = [lang["id"] for lang in payload["languages"]]
    assert lang_ids == ["python", "sql", "html", "javascript", "java", "c", "cpp"]

    expected_categories = {
        "hello",
        "variables",
        "condition",
        "loop",
        "function",
        "practical",
    }

    for lang in payload["languages"]:
        assert len(lang["examples"]) == 6
        assert {ex["category"] for ex in lang["examples"]} == expected_categories
        assert lang["status_label"] in ("Available", "Not installed")
        assert lang["mode_label"] in ("Runnable", "View only")
        for ex in lang["examples"]:
            assert ex["title"]
            assert ex["explanation"]
            assert ex["code"]
            assert ex["expected_output"]
            assert ex["mode_label"] == lang["mode_label"]

    # 2. Verify Python, SQL, and HTML/CSS execution via /api/v1/run
    py_run = client.post("/api/v1/run", json={
        "language": "python",
        "code": "print('Hello, Code Wizard!')"
    })
    assert py_run.status_code == 200
    py_data = py_run.json()
    assert py_data["ran"] is True
    assert py_data["success"] is True
    assert "Hello, Code Wizard!" in py_data["output"]

    sql_run = client.post("/api/v1/run", json={
        "language": "sql",
        "code": "SELECT 'SQLite Ready' AS status;"
    })
    assert sql_run.status_code == 200
    sql_data = sql_run.json()
    assert sql_data["ran"] is True
    assert sql_data["success"] is True
    assert "SQLite Ready" in sql_data["output"]

    html_run = client.post("/api/v1/run", json={
        "language": "html",
        "code": "<h1>Preview Heading</h1>"
    })
    assert html_run.status_code == 200
    html_data = html_run.json()
    assert html_data["ran"] is True
    assert html_data["success"] is True
    assert "<h1>Preview Heading</h1>" in html_data["html_preview"]


def test_simplified_student_dashboard_and_admin_students_skillproof():
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    html = html_resp.text

    # 1. Student Dashboard simplified: Continue Mission is main action, host toolchain bar removed
    assert 'id="hero-continue-btn"' in html
    assert "Continue Mission" in html
    assert 'id="dashboard-runtime-bar"' not in html
    assert "Host Toolchains:" not in html

    # 2. SkillProof hidden from student navigation while preserving SkillProof view & backend data
    assert 'id="nav-skillproof-li" style="display: none;" hidden' in html
    assert 'id="view-skillproof"' in html
    sp_resp = client.get("/api/skillproof")
    assert sp_resp.status_code == 200
    assert "evidence_records" in sp_resp.json()

    # 3. Admin Console contains "Students" tab and student profile / SkillProof lookup
    assert 'data-admin-tab="students"' in html
    assert 'id="admin-pane-students"' in html
    assert 'id="admin-student-search-input"' in html
    assert 'id="admin-student-profile-panel"' in html
    assert 'id="admin-prof-skillproof-list"' in html

    # 4. Student role cannot access staff student directory or profile SkillProof lookup
    stu_login = client.post("/api/v1/auth/login", json={
        "identifier": "alex.vance@campus.edu",
        "password": "Student@Pass2026!"
    })
    assert stu_login.status_code == 200
    stu_headers = {"Authorization": f"Bearer {stu_login.json()['token']}"}
    assert client.get("/api/v1/admin/students", headers=stu_headers).status_code == 403
    assert client.get("/api/v1/admin/students/stu_alex_vance/profile", headers=stu_headers).status_code == 403

    # 5. Teacher and Owner can search students and inspect a student's profile + SkillProof records
    teacher_login = client.post("/api/v1/auth/login", json={
        "identifier": "turing@campus.edu",
        "password": "Teacher@Pass2026!"
    })
    assert teacher_login.status_code == 200
    teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['token']}"}
    list_resp = client.get("/api/v1/admin/students?q=alex", headers=teacher_headers)
    assert list_resp.status_code == 200
    students = list_resp.json()["students"]
    assert any(s["id"] == "stu_alex_vance" for s in students)

    prof_resp = client.get("/api/v1/admin/students/stu_alex_vance/profile", headers=teacher_headers)
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()
    assert prof_data["student"]["id"] == "stu_alex_vance"
    assert "skillproof_records" in prof_data
    assert isinstance(prof_data["skillproof_records"], list)
    assert len(prof_data["skillproof_records"]) >= 1
    assert prof_data["skillproof_records"][0]["status"] == "Verified"
    assert "verification_source" in prof_data["skillproof_records"][0]


def test_common_student_error_topics_panel_and_telemetry():
    # 1. Verify HTML structure for Admin Common Student Error Topics panel
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    html = html_resp.text

    assert 'id="admin-common-errors-panel"' in html
    assert "Common Student Error Topics" in html
    assert 'id="admin-errors-source-badge"' in html
    assert 'id="admin-errors-note"' in html
    assert "Aggregated sandbox test-run errors for instructor review" in html
    assert 'id="admin-error-challenge-filter"' in html
    assert 'id="admin-error-category-filter"' in html
    assert 'id="admin-errors-summary-count"' in html
    assert 'id="admin-common-errors-list"' in html
    assert "Real-time Telemetry" not in html
    assert "Targeted AI coaching topics" not in html

    # 2. Verify staff can fetch Common Student Error Topics with occurrences, challenge, lesson, and category
    teacher_login = client.post("/api/v1/auth/login", json={
        "identifier": "turing@campus.edu",
        "password": "Teacher@Pass2026!"
    })
    assert teacher_login.status_code == 200
    teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['token']}"}

    overview_resp = client.get("/api/v1/admin/overview", headers=teacher_headers)
    assert overview_resp.status_code == 200
    overview = overview_resp.json()

    assert "common_errors" in overview
    assert "telemetry_source" in overview
    assert "telemetry_status_label" in overview
    assert "is_sample_data" in overview
    assert "telemetry_note" in overview
    assert overview["telemetry_status_label"] in ("Aggregated Sandbox Data", "Sample Data")

    errors = overview["common_errors"]
    assert len(errors) >= 1

    # Verify ranked order and required fields without any student PII
    prev_freq = float("inf")
    for idx, item in enumerate(errors, start=1):
        assert item["rank"] == idx
        assert "challenge_id" in item
        assert "challenge_title" in item and item["challenge_title"]
        assert "related_lesson" in item and item["related_lesson"]
        assert "error_category" in item and item["error_category"]
        assert "error_summary" in item and item["error_summary"]
        assert "frequency" in item and item["frequency"] >= 1
        assert item["count"] == item["frequency"]
        assert item["frequency"] <= prev_freq
        prev_freq = item["frequency"]

        # Privacy check: no student identity fields exposed
        assert "student_id" not in item
        assert "account_id" not in item
        assert "email" not in item
        assert "display_name" not in item


def test_student_directory_layout_and_actions_column():
    html = client.get("/").text
    css = client.get("/static/css/style.css").text
    app_js = client.get("/static/js/app.js").text

    # 1. Scrollable container and column class in HTML
    assert 'class="admin-students-table-wrap"' in html
    assert 'class="data-table admin-students-table"' in html
    assert 'class="col-student-actions"' in html

    # 2. CSS prevents button shrinking, vertical text wrapping, and clipping, plus mobile stacked cards
    assert ".admin-students-table-wrap" in css
    assert "overflow-x: auto" in css
    assert ".student-actions-cell" in css
    assert "min-width: 185px" in css
    assert ".student-actions-group .btn" in css
    assert "white-space: nowrap" in css
    assert "flex-shrink: 0" in css
    assert "content: attr(data-label)" in css

    # 3. JS renders concise "View profile" and separate "Edit" buttons with mobile data-label attributes
    assert 'data-label="Actions"' in app_js
    assert 'class="student-actions-group"' in app_js
    assert "View profile" in app_js
    assert "Open Profile &amp; SkillProof" not in app_js


def test_role_based_portal_routing_and_session_isolation():
    html = client.get("/").text
    app_js = client.get("/static/js/app.js").text
    api_js = client.get("/static/js/api.js").text

    # 1. Admin view is hidden by default in HTML
    assert '<section id="view-admin" class="view-section" hidden>' in html

    # 2. API setSession clears both sessionStorage and localStorage to prevent stale role collisions
    assert "[sessionStorage, localStorage].forEach" in api_js
    assert "store.removeItem('cm_session_token')" in api_js

    # 3. Role-based routing helpers in app.js use account.role (student -> languages, teacher/owner -> admin)
    assert "isStaffRole(" in app_js
    assert "getDefaultViewForRole(" in app_js
    assert "getDefaultHashForRole(" in app_js
    assert "return this.isStaffRole(account) ? 'admin' : 'languages';" in app_js
    assert "return this.isStaffRole(account) ? '#admin' : '#languages';" in app_js
    assert "role === 'owner' || role === 'teacher'" in app_js
    assert "btn-lang-lessons" in app_js
    assert "btn-lang-examples" in app_js
    assert "btn-lang-workspace" in app_js
    assert "btn-try-lesson-workspace" in app_js

    # 4. Auto-login helper routes clear both storages and use valid seeded accounts
    for route_path, expected_hash in [("/student", "#languages"), ("/teacher", "#admin"), ("/owner", "#admin")]:
        resp = client.get(route_path)
        assert resp.status_code == 200
        body = resp.text
        assert "sessionStorage.removeItem(k)" in body
        assert "localStorage.removeItem(k)" in body
        assert expected_hash in body

    # 5. Verify backend /api/v1/auth/me returns authoritative role for student, teacher, and owner
    for email, password, expected_role in [
        ("sugam@gmail.com", "Sugam@2026!", "student"),
        ("alex.vance@campus.edu", "Student@Pass2026!", "student"),
        ("turing@campus.edu", "Teacher@Pass2026!", "teacher"),
        ("owner@codemirror.local", "Admin@Pass2026!", "owner"),
    ]:
        login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        assert login_res.json()["account"]["role"] == expected_role

        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["account"]["role"] == expected_role

        admin_res = client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {token}"})
        if expected_role == "student":
            assert admin_res.status_code == 403
        else:
            assert admin_res.status_code == 200


def test_staff_portal_student_management_and_learning_programs():
    html = client.get("/").text
    assert 'id="admin-active-programs"' in html
    assert 'id="admin-completed-labs"' in html
    assert 'id="admin-recent-progress-panel"' in html
    assert 'id="admin-prof-programs-section"' in html
    assert 'id="admin-assign-program-select"' in html
    assert 'id="admin-assign-program-btn"' in html
    assert 'id="student-assigned-programs-section"' in html

    # Login as Teacher (Prof. Alan Turing) and Student (Alex Vance)
    teacher_login = client.post("/api/v1/auth/login", json={"email": "turing@campus.edu", "password": "Teacher@Pass2026!"})
    assert teacher_login.status_code == 200
    teacher_headers = {"Authorization": f"Bearer {teacher_login.json()['token']}"}

    student_login = client.post("/api/v1/auth/login", json={"email": "alex.vance@campus.edu", "password": "Student@Pass2026!"})
    assert student_login.status_code == 200
    student_headers = {"Authorization": f"Bearer {student_login.json()['token']}"}

    # 1. Staff Overview includes total students, active programs, completed labs, and recent progress
    ov_res = client.get("/api/v1/admin/overview", headers=teacher_headers)
    assert ov_res.status_code == 200
    ov_data = ov_res.json()
    assert "active_programs" in ov_data["metrics"]
    assert "completed_labs" in ov_data["metrics"]
    assert "recent_progress" in ov_data
    assert "program_summary" in ov_data

    # 2. Staff can assign and remove learning programs from the language catalog (persisted in DB)
    assign_res = client.post(
        "/api/v1/admin/students/stu_alex_vance/programs",
        headers=teacher_headers,
        json={"language_id": "java"}
    )
    assert assign_res.status_code == 200
    assigned_ids = [p["language_id"] for p in assign_res.json()["assigned_programs"]]
    assert "java" in assigned_ids

    # Student immediately sees their updated assigned programs on their own progress endpoint
    stu_prog = client.get("/api/v1/students/stu_alex_vance/progress", headers=student_headers)
    assert stu_prog.status_code == 200
    stu_prog_data = stu_prog.json()
    assert any(p["language_id"] == "java" for p in stu_prog_data["assigned_programs"])
    for p in stu_prog_data["assigned_programs"]:
        assert p["status"] in ("Completed", "In Progress", "Assigned")
        assert "progress_percent" in p

    # Student cannot view another student's progress or programs, nor assign programs
    assert client.get("/api/v1/students/stu_maya_lin/progress", headers=student_headers).status_code == 403
    assert client.get("/api/v1/students/stu_maya_lin/programs", headers=student_headers).status_code == 403
    assert client.post(
        "/api/v1/admin/students/stu_alex_vance/programs",
        headers=student_headers,
        json={"language_id": "c"}
    ).status_code == 403

    # Remove the assigned 'java' program and verify removal persists
    del_res = client.delete("/api/v1/admin/students/stu_alex_vance/programs/java", headers=teacher_headers)
    assert del_res.status_code == 200
    assert all(p["language_id"] != "java" for p in del_res.json()["assigned_programs"])

    # 3. Authorized staff can edit student details via PUT /api/v1/admin/students/{student_id}
    upd_res = client.put(
        "/api/v1/admin/students/stu_alex_vance",
        headers=teacher_headers,
        json={
            "display_name": "PixelPioneer (Alex)",
            "email": "alex.vance@campus.edu",
            "class_id": "cls_cs101",
            "assigned_programs": ["python", "sql", "html"]
        }
    )
    assert upd_res.status_code == 200
    assert {p["language_id"] for p in upd_res.json()["assigned_programs"]} == {"python", "sql", "html"}




