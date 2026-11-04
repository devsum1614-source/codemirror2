import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "password" not in data
    assert "db_path" not in data
    assert "secret" not in data


def test_challenges_catalog_hides_private_tests():
    resp = client.get("/api/v1/challenges")
    assert resp.status_code == 200
    challenges = resp.json()["challenges"]
    assert len(challenges) >= 5

    # Acceptance requirement: keep answer tests private to the server!
    for ch in challenges:
        assert "tests" not in ch
        assert "title" in ch
        assert "skill_tag" in ch
        assert "xp_reward" in ch
        assert "starter_code" in ch


def test_challenges_filtering_by_skill_and_level():
    resp_web = client.get("/api/v1/challenges?skill=web-validation")
    assert resp_web.status_code == 200
    items = resp_web.json()["challenges"]
    assert all(i["skill_tag"] == "web-validation" for i in items)

    resp_beg = client.get("/api/v1/challenges?level=beginner")
    assert resp_beg.status_code == 200
    items_beg = resp_beg.json()["challenges"]
    assert all(i["difficulty"].lower() == "beginner" for i in items_beg)


def test_attempt_submission_lifecycle_and_single_xp_reward():
    import uuid
    student_id = f"stu_test_{uuid.uuid4().hex[:8]}"
    
    # Register test student
    client.post("/api/v1/students", json={"display_name": "TestStudentOne"})
    
    # 1. Failed Attempt with buggy code
    buggy_code = """
def filter_resources(items, category=None, status="active"):
    return items # BUG: returns unfiltered
"""
    resp_fail = client.post(
        "/api/v1/attempts",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_py_filter",
            "code": buggy_code,
            "language": "python"
        }
    )
    assert resp_fail.status_code == 200
    data_fail = resp_fail.json()
    assert data_fail["passed"] is False
    assert data_fail["xp_earned"] == 0
    assert "att_" in data_fail["attempt_id"]

    # Verify attempt recorded in database
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT passed, error_summary FROM attempts WHERE id = ?", (data_fail["attempt_id"],))
    att_row = c.fetchone()
    assert att_row["passed"] == 0
    assert att_row["error_summary"] is not None

    # 2. Passing Attempt with correct code
    passing_code = """
from typing import List, Dict, Optional
VALID_STATUSES = {"active", "archived", "all"}

def filter_resources(items: List[Dict], category: Optional[str] = None, status: str = "active") -> List[Dict]:
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status filter")
    res = []
    cat_lower = category.lower().strip() if category else None
    for i in items:
        if status != "all" and i.get("status") != status:
            continue
        if cat_lower and i.get("category", "").lower().strip() != cat_lower:
            continue
        res.append(dict(i))
    return res
"""
    resp_pass = client.post(
        "/api/v1/attempts",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_py_filter",
            "code": passing_code,
            "language": "python"
        }
    )
    assert resp_pass.status_code == 200
    data_pass = resp_pass.json()
    assert data_pass["passed"] is True
    assert data_pass["xp_earned"] == 75 # Awarded once!
    assert data_pass["progress"]["total_xp"] >= 75
    assert data_pass["progress"]["level"] >= 1
    assert data_pass["progress"]["completed"] is True

    # 3. Repeated Passing Attempt -> XP Farming Protection: Must award 0 XP!
    resp_repeat = client.post(
        "/api/v1/attempts",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_py_filter",
            "code": passing_code,
            "language": "python"
        }
    )
    assert resp_repeat.status_code == 200
    data_repeat = resp_repeat.json()
    assert data_repeat["passed"] is True
    assert data_repeat["xp_earned"] == 0 # Must NOT award XP twice!
    assert data_repeat["progress"]["total_xp"] == data_pass["progress"]["total_xp"]

    conn.close()


def test_sandbox_timeout_safety():
    student_id = "stu_timeout_test"
    infinite_loop_code = """
def filter_resources(items, category=None, status="active"):
    while True:
        pass
"""
    resp = client.post(
        "/api/v1/attempts",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_py_filter",
            "code": infinite_loop_code,
            "language": "python"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is False
    assert data["xp_earned"] == 0
    assert "timed out" in data["feedback"].lower() or "limit exceeded" in data["feedback"].lower()


def test_ai_staged_hints_progression():
    import uuid
    student_id = f"stu_hints_{uuid.uuid4().hex[:8]}"
    
    # Stage 1: Question first
    h1_resp = client.post(
        "/api/v1/hints",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_web_validator",
            "hint_level": 1
        }
    )
    assert h1_resp.status_code == 200
    h1 = h1_resp.json()
    assert h1["hint_type"] == "question"
    assert "?" in h1["message"]

    # Stage 2: Clearer clue
    h2_resp = client.post(
        "/api/v1/hints",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_web_validator",
            "hint_level": 2
        }
    )
    assert h2_resp.status_code == 200
    h2 = h2_resp.json()
    assert h2["hint_type"] == "clue"

    # Stage 3: Full explanation
    h3_resp = client.post(
        "/api/v1/hints",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_web_validator",
            "hint_level": 3
        }
    )
    assert h3_resp.status_code == 200
    h3 = h3_resp.json()
    assert h3["hint_type"] == "explanation"

    # Verify hint event was saved to hint_events table
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM hint_events WHERE student_id = ?", (student_id,))
    count = c.fetchone()["count"]
    assert count == 3
    conn.close()


def test_student_progress_endpoint():
    import uuid
    student_id = f"stu_progress_{uuid.uuid4().hex[:8]}"
    
    # Check fresh student progress
    resp = client.get(f"/api/v1/students/{student_id}/progress")
    # If not registered, returns 404
    assert resp.status_code in [200, 404]

    # Post an attempt which registers the student
    sol = """
from typing import List, Dict, Optional
def filter_resources(items, category=None, status="active"):
    if status not in {"active", "archived", "all"}:
        raise ValueError("Invalid status filter")
    return [i for i in items if (status == 'all' or i.get('status') == status) and (not category or i.get('category','').lower() == category.lower())]
"""
    client.post("/api/v1/attempts", headers={"X-Student-Id": student_id}, json={
        "challenge_id": "ch_py_filter",
        "code": sol
    })

    resp_after = client.get(f"/api/v1/students/{student_id}/progress")
    assert resp_after.status_code == 200
    prog = resp_after.json()
    assert prog["student_id"] == student_id
    assert prog["total_xp"] >= 75
    assert prog["level"] == (prog["total_xp"] // 100) + 1
    assert prog["completed_count"] >= 1


def test_language_runtime_availability_check():
    import uuid
    student_id = f"stu_lang_{uuid.uuid4().hex[:8]}"

    # Runtimes endpoint check
    resp_rt = client.get("/api/v1/runtimes")
    assert resp_rt.status_code == 200
    runtimes = resp_rt.json()["runtimes"]
    assert "python" in runtimes
    assert "c" in runtimes
    assert runtimes["python"]["available"] is True

    # Test submitting C code without a C compiler -> must report runtime unavailable, never fake success!
    c_code = "int main() { return 0; }"
    resp = client.post(
        "/api/v1/attempts",
        headers={"X-Student-Id": student_id},
        json={
            "challenge_id": "ch_c_bounds",
            "code": c_code,
            "language": "c"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is False
    assert data["xp_earned"] == 0
    assert data["runtime_available"] is False
    assert "compiler is not installed" in data["feedback"] or "not found" in data["feedback"].lower()
