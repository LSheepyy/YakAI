"""Tests for ingestor/syllabus.py"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from ingestor.syllabus import (
    compute_syllabus_diff,
    extract_syllabus_data,
    save_syllabus_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _insert_class(db) -> str:
    semester_id = str(uuid.uuid4())
    class_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO semesters (id, name, user_id) VALUES (?, 'Fall 2026', 'u1')",
        (semester_id,),
    )
    await db.execute(
        """
        INSERT INTO classes
            (id, semester_id, course_code, course_name, slug, created_at)
        VALUES (?, ?, 'TEST101', 'Test Course', 'test101', ?)
        """,
        (class_id, semester_id, now),
    )
    await db.commit()
    return class_id


def _sample_syllabus_data() -> dict:
    return {
        "course": {"code": "TEST101", "name": "Test Course", "section": "01", "credits": "3", "schedule": "MWF"},
        "professor": {"name": "Dr. Test", "email": "test@uni.edu", "phone": "", "office": "ENG 100", "hours": "Mon 2–4pm"},
        "tas": [{"name": "Alice TA", "email": "alice@uni.edu", "hours": "Tue 1–3pm"}],
        "materials": [{"type": "textbook", "title": "Test Textbook", "author": "Smith", "edition": "3rd", "isbn": "1234567890"}],
        "grading": [
            {"component": "Midterm", "weight_pct": 30},
            {"component": "Final", "weight_pct": 40},
            {"component": "Assignments", "weight_pct": 30},
        ],
        "schedule": [
            {"week_or_date": "Week 1", "topic": "Introduction", "chapters": "Ch. 1"},
            {"week_or_date": "Week 2", "topic": "Deep Dive", "chapters": "Ch. 2"},
        ],
        "events": [
            {"title": "Midterm Exam", "date": "2026-10-15", "type": "exam", "location": "ENG 200"},
            {"title": "Assignment 1 Due", "date": "2026-09-20", "type": "assignment", "location": ""},
        ],
        "policies": {"late": "10% per day", "attendance": "Not mandatory", "integrity": "No collaboration"},
    }


# ---------------------------------------------------------------------------
# extract_syllabus_data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_syllabus_data_returns_placeholder_when_no_client():
    result = await extract_syllabus_data("some syllabus text", openai_client=None)
    assert isinstance(result, dict)
    assert "professor" in result
    assert "grading" in result
    assert "events" in result
    assert "schedule" in result


@pytest.mark.asyncio
async def test_extract_syllabus_data_placeholder_has_correct_keys():
    result = await extract_syllabus_data("text", openai_client=None)
    expected_keys = {"course", "professor", "tas", "materials", "grading", "schedule", "events", "policies"}
    assert expected_keys.issubset(set(result.keys()))


# ---------------------------------------------------------------------------
# save_syllabus_data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_syllabus_data_writes_professor_info(temp_db):
    class_id = await _insert_class(temp_db)
    data = _sample_syllabus_data()
    await save_syllabus_data(temp_db, class_id, data, source_file_id="file1")

    cursor = await temp_db.execute(
        "SELECT * FROM professor_info WHERE class_id = ?", (class_id,)
    )
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert dict(rows[0])["name"] == "Dr. Test"
    assert dict(rows[0])["email"] == "test@uni.edu"


@pytest.mark.asyncio
async def test_save_syllabus_data_writes_grading_weights(temp_db):
    class_id = await _insert_class(temp_db)
    data = _sample_syllabus_data()
    await save_syllabus_data(temp_db, class_id, data, source_file_id="file1")

    cursor = await temp_db.execute(
        "SELECT component, weight_pct FROM grading_weights WHERE class_id = ?",
        (class_id,),
    )
    rows = [dict(r) for r in await cursor.fetchall()]
    components = {r["component"] for r in rows}
    assert "Midterm" in components
    assert "Final" in components
    assert "Assignments" in components


@pytest.mark.asyncio
async def test_save_syllabus_data_creates_lecture_placeholders(temp_db):
    class_id = await _insert_class(temp_db)
    data = _sample_syllabus_data()
    await save_syllabus_data(temp_db, class_id, data, source_file_id="file1")

    cursor = await temp_db.execute(
        "SELECT * FROM lectures WHERE class_id = ?", (class_id,)
    )
    rows = await cursor.fetchall()
    assert len(rows) == 2
    titles = {dict(r)["title"] for r in rows}
    assert "Introduction" in titles
    assert "Deep Dive" in titles


@pytest.mark.asyncio
async def test_save_syllabus_data_writes_calendar_events(temp_db):
    class_id = await _insert_class(temp_db)
    data = _sample_syllabus_data()
    await save_syllabus_data(temp_db, class_id, data, source_file_id="file1")

    cursor = await temp_db.execute(
        "SELECT title FROM calendar_events WHERE class_id = ?", (class_id,)
    )
    rows = await cursor.fetchall()
    titles = {dict(r)["title"] for r in rows}
    assert "Midterm Exam" in titles
    assert "Assignment 1 Due" in titles


@pytest.mark.asyncio
async def test_save_syllabus_data_writes_ta_info(temp_db):
    class_id = await _insert_class(temp_db)
    data = _sample_syllabus_data()
    await save_syllabus_data(temp_db, class_id, data, source_file_id="file1")

    cursor = await temp_db.execute("SELECT name FROM ta_info WHERE class_id = ?", (class_id,))
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert dict(rows[0])["name"] == "Alice TA"


# ---------------------------------------------------------------------------
# compute_syllabus_diff
# ---------------------------------------------------------------------------

def test_diff_detects_added_event():
    old = {"events": [{"title": "Midterm", "date": "2026-10-15", "type": "exam"}]}
    new = {
        "events": [
            {"title": "Midterm", "date": "2026-10-15", "type": "exam"},
            {"title": "New Quiz", "date": "2026-09-30", "type": "quiz"},
        ]
    }
    diff = compute_syllabus_diff(old, new)
    assert len(diff["added"]) == 1
    assert diff["added"][0]["title"] == "New Quiz"
    assert diff["changed"] == []
    assert diff["removed"] == []


def test_diff_detects_removed_event():
    old = {
        "events": [
            {"title": "Midterm", "date": "2026-10-15", "type": "exam"},
            {"title": "Assignment 1", "date": "2026-09-20", "type": "assignment"},
        ]
    }
    new = {"events": [{"title": "Midterm", "date": "2026-10-15", "type": "exam"}]}
    diff = compute_syllabus_diff(old, new)
    assert len(diff["removed"]) == 1
    assert diff["removed"][0]["title"] == "Assignment 1"


def test_diff_detects_changed_event():
    old = {"events": [{"title": "Midterm", "date": "2026-10-15", "type": "exam"}]}
    new = {"events": [{"title": "Midterm", "date": "2026-10-22", "type": "exam"}]}  # date changed
    diff = compute_syllabus_diff(old, new)
    assert len(diff["changed"]) == 1
    assert diff["changed"][0]["date"] == "2026-10-22"


def test_diff_empty_both():
    diff = compute_syllabus_diff({"events": []}, {"events": []})
    assert diff == {"changed": [], "added": [], "removed": []}


def test_diff_no_changes():
    events = [{"title": "Midterm", "date": "2026-10-15", "type": "exam"}]
    diff = compute_syllabus_diff({"events": events}, {"events": events})
    assert diff == {"changed": [], "added": [], "removed": []}
