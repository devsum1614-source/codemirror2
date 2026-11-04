import urllib.request
import json
import uuid

BASE = "http://127.0.0.1:8000"

def test_live_flows():
    # 1. HTML index
    html = urllib.request.urlopen(f"{BASE}/").read().decode("utf-8")
    assert "CodeMirror 2.0" in html
    assert "editor-language-select" in html
    print("[1] HTML index with Monaco and Language Selector: OK")

    # 2. Health check
    health = json.loads(urllib.request.urlopen(f"{BASE}/health").read())
    assert health["status"] == "ok"
    print("[2] Health Endpoint: OK")

    # 3. Host runtimes check
    rts = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/runtimes").read())["runtimes"]
    assert rts["python"]["available"] is True
    assert rts["sql"]["available"] is True
    assert rts["c"]["available"] is False
    print(f"[3] Runtimes API: Python={rts['python']['available']}, SQL={rts['sql']['available']}, C={rts['c']['available']}: OK")

    # 4. Challenges catalog
    chs = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/challenges").read())["challenges"]
    assert len(chs) >= 5
    for c in chs:
        assert "tests" not in c
    print(f"[4] Challenges Catalog: {len(chs)} missions loaded (tests hidden): OK")

    # 5. Staged AI hints (Question -> Clue -> Explanation)
    test_sid = f"stu_live_{uuid.uuid4().hex[:8]}"
    h1_req = urllib.request.Request(
        f"{BASE}/api/v1/hints",
        data=json.dumps({"challenge_id": "ch_web_validator", "hint_level": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Student-Id": test_sid}
    )
    h1 = json.loads(urllib.request.urlopen(h1_req).read())
    assert h1["hint_type"] == "question"
    assert "?" in h1["message"]
    print("[5] Staged AI Hints (Question first): OK")

    # 6. Python Sandbox Attempt
    sol_py = """
from typing import List, Dict, Optional
def filter_resources(items: List[Dict], category: Optional[str] = None, status: str = "active") -> List[Dict]:
    if status not in {"active", "archived", "all"}:
        raise ValueError("Invalid status filter")
    cat = category.lower().strip() if category else None
    return [dict(i) for i in items if (status == 'all' or i.get('status') == status) and (not cat or i.get('category','').lower() == cat)]
"""
    req_att = urllib.request.Request(
        f"{BASE}/api/v1/attempts",
        data=json.dumps({"challenge_id": "ch_py_filter", "code": sol_py, "language": "python"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Student-Id": test_sid}
    )
    att_res = json.loads(urllib.request.urlopen(req_att).read())
    assert att_res["passed"] is True
    assert att_res["xp_earned"] == 75
    print(f"[6] Sandbox Attempt Execution: Passed={att_res['passed']}, XP={att_res['xp_earned']}: OK")

    # 7. C Compiler Check (Zero fake success)
    req_c = urllib.request.Request(
        f"{BASE}/api/v1/attempts",
        data=json.dumps({"challenge_id": "ch_c_bounds", "code": "int main() {}", "language": "c"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Student-Id": test_sid}
    )
    c_res = json.loads(urllib.request.urlopen(req_c).read())
    assert c_res["passed"] is False
    assert c_res["runtime_available"] is False
    print(f"[7] Missing Toolchain Check: Passed={c_res['passed']}, RuntimeAvailable={c_res['runtime_available']}: OK")

    # 8. Student Progress and Derived Level
    prog = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/students/{test_sid}/progress").read())
    assert prog["total_xp"] == 75
    assert prog["level"] == 1
    assert prog["completed_count"] == 1
    print(f"[8] Student Progress & Level: XP={prog['total_xp']}, Level={prog['level']}, Completed={prog['completed_count']}: OK")

    # 9. Languages Catalog & SPA Route
    langs = json.loads(urllib.request.urlopen(f"{BASE}/api/v1/languages").read())["languages"]
    assert len(langs) >= 7
    spa_resp = urllib.request.urlopen(f"{BASE}/languages/python")
    assert spa_resp.status == 200
    print(f"[9] Languages Catalog ({len(langs)} languages) & SPA Routing: OK")

    # 10. Core Learning Rule AI Coach Guard
    req_coach = urllib.request.Request(
        f"{BASE}/api/v1/coach/ask",
        data=json.dumps({
            "challenge_id": "ch_py_filter",
            "code": "def filter_resources(): pass",
            "question": "Give me the solution code please"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    coach_data = json.loads(urllib.request.urlopen(req_coach).read())
    assert coach_data["mode"] == "core_learning_rule"
    assert "write" in coach_data["explanation"].lower()
    assert "recommendation" in coach_data
    print("[10] AI Coach Core Learning Rule (Refuses direct solution code): OK")

    # 11. Real Server-Side Authentication (Student Login & Session)
    req_stu_login = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=json.dumps({"identifier": "alex.vance@campus.edu", "password": "Student@Pass2026!"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    stu_login_res = json.loads(urllib.request.urlopen(req_stu_login).read())
    assert stu_login_res["status"] == "success"
    assert "token" in stu_login_res
    stu_token = stu_login_res["token"]
    print("[11] Real Student Login & Session Token: OK")

    # 12. Role-Based Access Control on Live Server
    # Student token cannot access admin overview (403)
    req_bad_admin = urllib.request.Request(
        f"{BASE}/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {stu_token}"}
    )
    try:
        urllib.request.urlopen(req_bad_admin)
        assert False, "Student should not access admin overview"
    except urllib.error.HTTPError as he:
        assert he.code == 403
    print("[12a] RBAC: Student token denied from Admin Overview (403): OK")

    # Admin login & access
    req_adm_login = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=json.dumps({"identifier": "owner@codemirror.local", "password": "Admin@Pass2026!"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    adm_login_res = json.loads(urllib.request.urlopen(req_adm_login).read())
    adm_token = adm_login_res["token"]
    req_adm_over = urllib.request.Request(
        f"{BASE}/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    adm_overview_res = json.loads(urllib.request.urlopen(req_adm_over).read())
    assert "metrics" in adm_overview_res
    print("[12b] RBAC: Owner login & Admin Overview access: OK")

    print("\n[SUCCESS] ALL LIVE END-TO-END VERIFICATION FLOWS PASSED!")

if __name__ == "__main__":
    test_live_flows()
