import uuid

import pytest
from fastapi.testclient import TestClient

from app.curriculum import COURSES, COURSE_ORDER, LESSON_PATH, list_courses
from app.database import init_db
from app.main import app
from app.runtimes import check_language_runtime
from app.sandbox import execute_code_snippet

client = TestClient(app)

TOPICS = [topic for topic, _title in LESSON_PATH]
REQUIRED_COURSES = {"c", "cpp", "java", "python", "javascript", "typescript", "html"}


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    # login/register set a session cookie on the shared client; start every test signed out
    client.cookies.clear()


def anonymous():
    """A brand-new client with no cookie jar, i.e. a genuinely signed-out visitor."""
    return TestClient(app)


def _login(identifier, password):
    resp = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def _new_student():
    email = f"course_{uuid.uuid4().hex[:8]}@campus.edu"
    resp = client.post(
        "/api/v1/auth/register",
        json={"display_name": "Course Tester", "email": email, "password": "CourseTester2026!"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


# ---------------------------------------------------------------------------
# Content structure
# ---------------------------------------------------------------------------
def test_all_requested_courses_exist_with_the_same_ordered_path():
    assert set(COURSES) == REQUIRED_COURSES
    assert set(COURSE_ORDER) == REQUIRED_COURSES
    for course in list_courses():
        assert [lesson["topic"] for lesson in course["lessons"]] == TOPICS, course["id"]
        assert course["lessons"][0]["topic"] == "intro"
        assert course["lessons"][1]["topic"] == "hello"
        assert course["lessons"][-1]["topic"] == "project"


def test_every_lesson_has_explanation_example_and_exercise():
    seen = set()
    for course in list_courses():
        for lesson in course["lessons"]:
            assert lesson["id"] not in seen
            seen.add(lesson["id"])
            assert lesson["explanation"].strip(), lesson["id"]
            assert lesson["example"].strip(), lesson["id"]
            assert lesson["expected_output"].strip(), lesson["id"]
            assert lesson["exercise"]["prompt"].strip(), lesson["id"]
            assert lesson["exercise"]["starter"].strip(), lesson["id"]


def test_typescript_is_read_only_and_not_presented_as_runnable():
    resp = client.get("/api/v1/courses/typescript")
    assert resp.status_code == 200
    data = resp.json()
    assert data["runnable"] is False
    assert data["language"] is None
    assert "no typescript runner" in data["note"].lower()


# ---------------------------------------------------------------------------
# Public catalog
# ---------------------------------------------------------------------------
def test_catalog_is_public_and_starts_not_started():
    resp = anonymous().get("/api/v1/courses")
    assert resp.status_code == 200
    data = resp.json()
    assert data["signed_in"] is False
    assert {c["id"] for c in data["courses"]} == REQUIRED_COURSES
    for course in data["courses"]:
        assert course["lesson_count"] == 8
        assert course["status"] == "not_started"
        assert course["completed_count"] == 0
    assert [p["topic"] for p in data["lesson_path"]] == TOPICS


def test_unknown_course_is_404():
    assert client.get("/api/v1/courses/cobol").status_code == 404


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------
def test_student_progress_flow_not_started_in_progress_completed():
    headers = _new_student()

    detail = client.get("/api/v1/courses/python", headers=headers).json()
    assert detail["signed_in"] is True
    assert all(l["status"] == "not_started" for l in detail["lessons"])
    first, second = detail["lessons"][0]["id"], detail["lessons"][1]["id"]

    r = client.put(f"/api/v1/courses/python/lessons/{first}/progress", json={"status": "in_progress"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["course"]["status"] == "in_progress"
    assert r.json()["course"]["in_progress_count"] == 1

    r = client.put(f"/api/v1/courses/python/lessons/{first}/progress", json={"status": "completed"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["course"]["completed_count"] == 1
    assert r.json()["course"]["percent"] == 13  # 1 of 8
    assert r.json()["course"]["next_lesson_id"] == second

    detail = client.get("/api/v1/courses/python", headers=headers).json()
    statuses = {l["id"]: l["status"] for l in detail["lessons"]}
    assert statuses[first] == "completed"
    assert statuses[second] == "not_started"

    # Reset back to not started removes the row
    r = client.put(f"/api/v1/courses/python/lessons/{first}/progress", json={"status": "not_started"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["course"]["completed_count"] == 0

    # The catalog reflects the same learner's state
    catalog = client.get("/api/v1/courses", headers=headers).json()
    assert catalog["signed_in"] is True


def test_completing_every_lesson_completes_the_course():
    headers = _new_student()
    detail = client.get("/api/v1/courses/c", headers=headers).json()
    last = None
    for lesson in detail["lessons"]:
        last = client.put(
            f"/api/v1/courses/c/lessons/{lesson['id']}/progress", json={"status": "completed"}, headers=headers
        ).json()
    assert last["course"]["status"] == "completed"
    assert last["course"]["percent"] == 100
    assert last["course"]["next_lesson_id"] is None


def test_progress_is_isolated_between_students():
    alice, bob = _new_student(), _new_student()
    lesson_id = client.get("/api/v1/courses/java").json()["lessons"][0]["id"]
    client.put(f"/api/v1/courses/java/lessons/{lesson_id}/progress", json={"status": "completed"}, headers=alice)

    bob_view = client.get("/api/v1/courses/java", headers=bob).json()
    assert all(l["status"] == "not_started" for l in bob_view["lessons"])
    alice_view = client.get("/api/v1/courses/java", headers=alice).json()
    assert alice_view["lessons"][0]["status"] == "completed"


def test_progress_validation_and_access_control():
    headers = _new_student()
    lesson_id = client.get("/api/v1/courses/python").json()["lessons"][0]["id"]
    url = f"/api/v1/courses/python/lessons/{lesson_id}/progress"

    # Not signed in (fresh client: no cookie, no header)
    assert anonymous().put(url, json={"status": "completed"}).status_code == 401
    # Spoofed id header without a session is still rejected
    assert anonymous().put(url, json={"status": "completed"}, headers={"X-Account-Id": "stu_alex_vance"}).status_code == 401
    # Invalid status
    assert client.put(url, json={"status": "done!"}, headers=headers).status_code == 422
    # Unknown lesson / course, and a lesson that belongs to another course
    assert client.put("/api/v1/courses/python/lessons/nope/progress", json={"status": "completed"}, headers=headers).status_code == 404
    assert client.put("/api/v1/courses/cobol/lessons/x/progress", json={"status": "completed"}, headers=headers).status_code == 404
    assert client.put("/api/v1/courses/java/lessons/" + lesson_id + "/progress", json={"status": "completed"}, headers=headers).status_code == 404


def test_staff_cannot_write_learner_progress():
    teacher = _login("turing@campus.edu", "Teacher@Pass2026!")
    lesson_id = client.get("/api/v1/courses/python").json()["lessons"][0]["id"]
    resp = client.put(
        f"/api/v1/courses/python/lessons/{lesson_id}/progress", json={"status": "completed"}, headers=teacher
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Examples really run (only for toolchains installed on the machine running the tests)
# ---------------------------------------------------------------------------
def _runnable_languages():
    langs = []
    for lang in ("python", "javascript", "java", "c", "cpp"):
        if check_language_runtime(lang).get("available"):
            langs.append(lang)
    return langs


@pytest.mark.parametrize("course_id", ["python", "javascript", "java", "c", "cpp"])
def test_lesson_examples_produce_the_documented_output(course_id):
    if course_id not in _runnable_languages():
        pytest.skip(f"{course_id} toolchain is not installed on this machine")
    for lesson in COURSES[course_id]["lessons"]:
        result = execute_code_snippet(
            lesson["example"], language=course_id, stdin_text=lesson["sample_input"], timeout_seconds=10.0
        )
        assert result["success"], f"{lesson['id']}: {result.get('error')}"
        got = [line.rstrip() for line in result["output"].strip().splitlines()]
        want = [line.rstrip() for line in lesson["expected_output"].strip().splitlines()]
        assert got == want, f"{lesson['id']}: expected {want!r}, got {got!r}"
