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
