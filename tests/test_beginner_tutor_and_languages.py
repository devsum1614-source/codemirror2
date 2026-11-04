import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from app.seed_challenges import seed_quest_data

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    seed_quest_data()

def test_languages_catalog_endpoint():
    resp = client.get("/api/v1/languages")
    assert resp.status_code == 200
    data = resp.json()
    assert "languages" in data
    langs = {l["id"]: l for l in data["languages"]}
    
    # Must include core languages
    assert "python" in langs
    assert "sql" in langs
    assert "html" in langs
    assert "javascript" in langs
    assert "java" in langs
    assert "c" in langs
    assert "cpp" in langs

    # Python & SQL & HTML must be available on host
    assert langs["python"]["available"] is True
    assert langs["sql"]["available"] is True
    assert langs["html"]["available"] is True
    assert langs["python"]["challenges_count"] >= 1

def test_language_details_endpoint():
    # Python details
    py_resp = client.get("/api/v1/languages/python")
    assert py_resp.status_code == 200
    py_data = py_resp.json()
    assert py_data["id"] == "python"
    assert len(py_data["lessons"]) >= 3
    assert len(py_data["examples"]) >= 1
    assert "setup_guide" in py_data
    assert len(py_data["challenges"]) >= 1

    # Java details
    java_resp = client.get("/api/v1/languages/java")
    assert java_resp.status_code == 200
    java_data = java_resp.json()
    assert java_data["id"] == "java"
    assert "setup_guide" in java_data
    assert len(java_data["lessons"]) >= 2

def test_challenges_filtered_by_language():
    resp = client.get("/api/v1/challenges?language=python")
    assert resp.status_code == 200
    challenges = resp.json()["challenges"]
    assert len(challenges) >= 1
    for ch in challenges:
        skill = ch["skill_tag"].lower()
        ch_id = ch["id"].lower()
        assert "python" in skill or "backend" in skill or "py" in ch_id or ch.get("execution_language") == "python"

def test_core_learning_rule_guards_against_solution_requests():
    # When a student asks the AI for the full code or solution
    payload = {
        "challenge_id": "ch_py_filter",
        "code": "def filter_resources(): pass",
        "question": "Please give me the solution code for this lab."
    }
    resp = client.post("/api/v1/coach/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    # Must enforce Core Learning Rule and refuse to generate solution
    assert data["mode"] == "core_learning_rule"
    assert "Core Learning Rule" in data["explanation"]
    assert "cannot write" in data["explanation"] or "tutor" in data["explanation"]
    assert "def filter_resources" not in data["explanation"]

def test_socratic_syntax_guidance():
    # When a student asks how syntax works
    payload = {
        "challenge_id": "ch_py_filter",
        "code": "def filter_resources(): pass",
        "question": "Can you show me an example of how an if statement works in Python?"
    }
    resp = client.post("/api/v1/coach/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "syntax_guidance"
    assert "generic syntax reference" in data["explanation"]
    assert "does not solve your specific lab" in data["explanation"]

def test_socratic_error_debugging_assistance():
    # When a student has a test error
    payload = {
        "challenge_id": "ch_c_bounds",
        "code": "def calculate_average_rating(scores): return sum(scores) / len(scores)",
        "question": "Why did my test fail?",
        "recent_error": "ZeroDivisionError: division by zero (line 2)"
    }
    resp = client.post("/api/v1/coach/ask", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "debugging_assistance"
    assert "line 2" in data["explanation"]
    assert "What line of code could you adjust" in data["recommendation"]

def test_spa_language_routes_serve_index():
    # Check that navigating directly to /languages and /languages/python returns 200 with HTML
    res1 = client.get("/languages")
    assert res1.status_code == 200
    assert "text/html" in res1.headers["content-type"]

    res2 = client.get("/languages/python")
    assert res2.status_code == 200
    assert "text/html" in res2.headers["content-type"]
