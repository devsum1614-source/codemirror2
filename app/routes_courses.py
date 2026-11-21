"""
Beginner courses API (stage 2 of the learning platform).

    GET  /api/v1/courses                                   course list (+ your progress if signed in)
    GET  /api/v1/courses/{course_id}                       one course with all lessons (+ your status)
    PUT  /api/v1/courses/{course_id}/lessons/{lesson_id}/progress
                                                           set not_started / in_progress / completed

Lesson content is public (it is teaching material). Progress belongs to the signed-in
learner: it is always read and written for the authenticated account taken from the session,
never from a client-supplied id, and staff accounts cannot write learner progress.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import get_current_account, get_optional_account
from app.curriculum import (
    LESSON_PATH,
    LESSON_STATUSES,
    find_lesson,
    get_course,
    list_courses,
)
from app.database import get_db
from app.runtimes import check_language_runtime

router = APIRouter(prefix="/api/v1/courses")


class LessonProgressRequest(BaseModel):
    status: str


def _progress_map(student_id: str, course_id: str = None) -> Dict[str, str]:
    """lesson_id -> status for this learner. Missing lessons are 'not_started'."""
    if not student_id:
        return {}
    conn = get_db()
    try:
        if course_id:
            rows = conn.execute(
                "SELECT lesson_id, status FROM lesson_progress WHERE student_id = ? AND course_id = ?",
                (student_id, course_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT lesson_id, status FROM lesson_progress WHERE student_id = ?", (student_id,)
            ).fetchall()
        return {row["lesson_id"]: row["status"] for row in rows}
    finally:
        conn.close()


def _runtime_info(course: Dict[str, Any]) -> Dict[str, Any]:
    language = course.get("language")
    if not language:
        return {
            "runnable": False,
            "runtime_label": "No runner installed",
            "note": course.get("read_only_note", "This course is read-only on this server."),
        }
    info = check_language_runtime(language)
    available = bool(info.get("available"))
    return {
        "runnable": available,
        "runtime_label": info.get("runtime_label", course["name"]),
        "note": "" if available else (
            f"The {course['name']} toolchain is not installed on this server, so examples are view-only here."
        ),
    }


def _summarize(course: Dict[str, Any], progress: Dict[str, str]) -> Dict[str, Any]:
    lessons = course["lessons"]
    completed = sum(1 for l in lessons if progress.get(l["id"]) == "completed")
    in_progress = sum(1 for l in lessons if progress.get(l["id"]) == "in_progress")
    if completed == len(lessons):
        status = "completed"
    elif completed or in_progress:
        status = "in_progress"
    else:
        status = "not_started"
    next_lesson = next((l for l in lessons if progress.get(l["id"]) != "completed"), None)
    return {
        "id": course["id"],
        "name": course["name"],
        "icon": course["icon"],
        "tagline": course["tagline"],
        "lesson_count": len(lessons),
        "completed_count": completed,
        "in_progress_count": in_progress,
        "percent": (100 * completed + len(lessons) // 2) // len(lessons) if lessons else 0,
        "status": status,
        "next_lesson_id": next_lesson["id"] if next_lesson else None,
        **_runtime_info(course),
    }


@router.get("")
def list_course_catalog(request: Request):
    account = get_optional_account(request)
    is_learner = bool(account and account.get("role") == "student")
    progress = _progress_map(account["id"]) if is_learner else {}
    return {
        "signed_in": is_learner,
        "courses": [_summarize(course, progress) for course in list_courses()],
        "lesson_path": [{"topic": topic, "title": title} for topic, title in LESSON_PATH],
    }


@router.get("/{course_id}")
def get_course_detail(course_id: str, request: Request):
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found.")

    account = get_optional_account(request)
    is_learner = bool(account and account.get("role") == "student")
    progress = _progress_map(account["id"], course["id"]) if is_learner else {}

    lessons: List[Dict[str, Any]] = []
    for lesson in course["lessons"]:
        item = dict(lesson)
        item["status"] = progress.get(lesson["id"], "not_started")
        lessons.append(item)

    summary = _summarize(course, progress)
    return {
        **summary,
        "language": course.get("language"),
        "file_ext": course.get("file_ext"),
        "signed_in": is_learner,
        "lessons": lessons,
    }


@router.put("/{course_id}/lessons/{lesson_id}/progress")
def set_lesson_progress(
    course_id: str,
    lesson_id: str,
    body: LessonProgressRequest,
    account: Dict[str, Any] = Depends(get_current_account),
):
    # Learner progress is for learners only; the staff portal has its own tools.
    if account.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only student accounts can record lesson progress.")

    course = get_course(course_id)
    lesson = find_lesson(course_id, lesson_id) if course else None
    if not course or not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    status = (body.status or "").strip().lower()
    if status not in LESSON_STATUSES:
        raise HTTPException(
            status_code=422, detail=f"status must be one of: {', '.join(LESSON_STATUSES)}."
        )

    conn = get_db()
    try:
        if status == "not_started":
            conn.execute(
                "DELETE FROM lesson_progress WHERE student_id = ? AND lesson_id = ?",
                (account["id"], lesson_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO lesson_progress (student_id, course_id, lesson_id, status, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, lesson_id)
                DO UPDATE SET status = excluded.status, updated_at = CURRENT_TIMESTAMP
                """,
                (account["id"], course["id"], lesson_id, status),
            )
        conn.commit()
    finally:
        conn.close()

    progress = _progress_map(account["id"], course["id"])
    return {
        "lesson_id": lesson_id,
        "status": status,
        "course": _summarize(course, progress),
    }
