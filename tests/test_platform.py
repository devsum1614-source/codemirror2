import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.runner import run_tests_for_mission
from app.ai_coach import get_hint, explain_code_context

client = TestClient(app)

def test_user_endpoint():
    resp = client.get("/api/user")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert data["name"] == "Alex Vance"

def test_missions_list():
    resp = client.get("/api/missions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["missions"]) >= 5
    mission_ids = [m["mission_id"] for m in data["missions"]]
    assert "web-validate-title" in mission_ids
    assert "sql-resource-search" in mission_ids
    assert "py-api-filter" in mission_ids
    assert "c-off-by-one" in mission_ids

def test_web_validate_mission_lifecycle():
    # 1. Fetch detail
    resp = client.get("/api/missions/web-validate-title")
    assert resp.status_code == 200
    detail = resp.json()
    assert "validateResourceTitle" in detail["starter_code"]

    # 2. Run tests on buggy starter code -> should fail tests
    run_resp = client.post("/api/missions/web-validate-title/run-tests", json={
        "code": detail["starter_code"]
    })
    assert run_resp.status_code == 200
    starter_res = run_resp.json()
    assert starter_res["all_passed"] is False
    assert starter_res["failed_count"] > 0

    # 3. Progressive hints
    h1 = get_hint("web-validate-title", 1)
    h2 = get_hint("web-validate-title", 2)
    h3 = get_hint("web-validate-title", 3)
    assert h1["level"] == 1
    assert "trim" in h2["message"].lower()

    # 4. Run tests with solution code -> all pass
    sol_resp = client.post("/api/missions/web-validate-title/run-tests", json={
        "code": detail["solution_code"]
    })
    assert sol_resp.status_code == 200
    sol_res = sol_resp.json()
    assert sol_res["all_passed"] is True
    assert sol_res["passed_count"] == sol_res["total_count"]

    # 5. Submit mission with explanation
    sub_resp = client.post("/api/missions/web-validate-title/submit", json={
        "code": detail["solution_code"],
        "explanation": "Added trim() and enforced minimum length of 3 and maximum 50 characters to prevent invalid empty titles."
    })
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["status"] == "completed"
    assert sub_data["score"] >= 80

def test_sql_resource_search():
    sol_query = """
    SELECT resources.id, resources.title, categories.name AS category_name, resources.created_at
    FROM resources
    INNER JOIN categories ON resources.category_id = categories.id
    WHERE resources.status = 'active'
    ORDER BY resources.created_at DESC;
    """
    res = run_tests_for_mission("sql-resource-search", sol_query)
    assert res["all_passed"] is True
    assert res["passed_count"] == 4

def test_py_api_filter():
    code = """
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
    res = run_tests_for_mission("py-api-filter", code)
    assert res["all_passed"] is True
    assert res["passed_count"] == 5

def test_c_off_by_one_fix():
    c_code = """
double calculate_average_rating(const int scores[], int count) {
    if (count <= 0 || scores == NULL) {
        return 0.0;
    }
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += scores[i];
    }
    return sum / (double)count;
}
"""
    res = run_tests_for_mission("c-off-by-one", c_code)
    assert res["all_passed"] is True
    assert res["passed_count"] == 3

def test_skillproof_and_report_endpoints():
    sp_resp = client.get("/api/skillproof")
    assert sp_resp.status_code == 200
    rep_resp = client.get("/api/learning-report")
    assert rep_resp.status_code == 200
