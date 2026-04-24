"""
Semester and class management routes.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime
from typing import Any

import aiosqlite
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from brain.builder import generate_brain_file, write_brain_file
from db.schema import get_db

router = APIRouter(tags=["classes"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateSemesterRequest(BaseModel):
    name: str
    user_id: str


class CreateClassRequest(BaseModel):
    semester_id: str
    course_code: str
    course_name: str
    professor: str | None = None
    major: str | None = None
    slug: str | None = None


class UpdateClassRequest(BaseModel):
    course_name: str | None = None
    professor: str | None = None
    major: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_slug(course_code: str, course_name: str) -> str:
    base = f"{course_code}-{course_name}".lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


async def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    return dict(row)


# ---------------------------------------------------------------------------
# Semester routes
# ---------------------------------------------------------------------------

@router.post("/semesters", status_code=201)
async def create_semester(body: CreateSemesterRequest, request: Request) -> dict:
    db_path: str = request.app.state.db_path
    now = datetime.utcnow().isoformat()
    semester_id = str(uuid.uuid4())

    async with get_db(db_path) as db:
        await db.execute(
            "INSERT INTO semesters (id, name, user_id) VALUES (?, ?, ?)",
            (semester_id, body.name, body.user_id),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, name, user_id FROM semesters WHERE id = ?", (semester_id,)
        )
        row = await cursor.fetchone()

    return dict(row)


@router.get("/semesters")
async def list_semesters(request: Request) -> list[dict]:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id, name, user_id FROM semesters")
        semesters = [dict(r) for r in await cursor.fetchall()]

        for sem in semesters:
            cls_cursor = await db.execute(
                "SELECT * FROM classes WHERE semester_id = ? ORDER BY created_at",
                (sem["id"],),
            )
            sem["classes"] = [dict(r) for r in await cls_cursor.fetchall()]

    return semesters


# ---------------------------------------------------------------------------
# Class routes
# ---------------------------------------------------------------------------

@router.post("/classes", status_code=201)
async def create_class(body: CreateClassRequest, request: Request) -> dict:
    db_path: str = request.app.state.db_path
    app_data: str = request.app.state.app_data
    now = datetime.utcnow().isoformat()
    class_id = str(uuid.uuid4())
    slug = body.slug or _make_slug(body.course_code, body.course_name)

    # Resolve semester name for directory
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM semesters WHERE id = ?", (body.semester_id,)
        )
        sem_row = await cursor.fetchone()
        if sem_row is None:
            raise HTTPException(status_code=404, detail="Semester not found")
        semester_name = sem_row["name"]

    # Build BRAIN file path
    safe_semester = re.sub(r"[^a-zA-Z0-9_-]", "-", semester_name)
    brain_dir = os.path.join(app_data, "data", safe_semester, slug)
    brain_path = os.path.join(brain_dir, f"{slug}.md")

    # Generate and write BRAIN file
    class_info = {
        "slug": slug,
        "course_code": body.course_code,
        "course_name": body.course_name,
        "professor": body.professor,
        "semester": semester_name,
        "major": body.major,
    }
    brain_content = generate_brain_file(class_info)
    await write_brain_file(brain_path, brain_content)

    async with get_db(db_path) as db:
        await db.execute(
            """
            INSERT INTO classes
                (id, semester_id, course_code, course_name, slug, professor,
                 major, brain_file_path, is_archived, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                class_id, body.semester_id, body.course_code, body.course_name,
                slug, body.professor, body.major, brain_path, now,
            ),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()

    return dict(row)


@router.get("/classes/{class_id}")
async def get_class(class_id: str, request: Request) -> dict:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Class not found")
        data = dict(row)

        # Professor info
        cur = await db.execute(
            "SELECT * FROM professor_info WHERE class_id = ? LIMIT 1", (class_id,)
        )
        prof_row = await cur.fetchone()
        data["professor_info"] = dict(prof_row) if prof_row else None

        # TA info
        cur = await db.execute("SELECT * FROM ta_info WHERE class_id = ?", (class_id,))
        data["ta_info"] = [dict(r) for r in await cur.fetchall()]

        # Grading weights
        cur = await db.execute(
            "SELECT * FROM grading_weights WHERE class_id = ? ORDER BY weight_pct DESC",
            (class_id,),
        )
        data["grading_weights"] = [dict(r) for r in await cur.fetchall()]

        # Lectures
        cur = await db.execute(
            "SELECT * FROM lectures WHERE class_id = ? ORDER BY number, date",
            (class_id,),
        )
        data["lectures"] = [dict(r) for r in await cur.fetchall()]

        # Required materials
        cur = await db.execute(
            "SELECT * FROM required_materials WHERE class_id = ?", (class_id,)
        )
        data["required_materials"] = [dict(r) for r in await cur.fetchall()]

    return data


@router.patch("/classes/{class_id}")
async def update_class(class_id: str, body: UpdateClassRequest, request: Request) -> dict:
    db_path: str = request.app.state.db_path
    updates: dict[str, Any] = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [class_id]

    async with get_db(db_path) as db:
        await db.execute(f"UPDATE classes SET {set_clause} WHERE id = ?", values)
        await db.commit()
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Class not found")

    return dict(row)


@router.delete("/classes/{class_id}", status_code=204, response_model=None)
async def delete_class(class_id: str, request: Request) -> None:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT brain_file_path FROM classes WHERE id = ?", (class_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Class not found")
        brain_path = row["brain_file_path"]

        # Delete in FK-safe order (child tables first)
        await db.execute(
            """
            DELETE FROM quiz_attempts WHERE question_id IN (
                SELECT qq.id FROM quiz_questions qq
                JOIN quiz_sessions qs ON qq.session_id = qs.id
                WHERE qs.class_id = ?
            )
            """,
            (class_id,),
        )
        await db.execute(
            "DELETE FROM quiz_questions WHERE session_id IN (SELECT id FROM quiz_sessions WHERE class_id = ?)",
            (class_id,),
        )
        await db.execute("DELETE FROM quiz_sessions WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM chat_messages WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM calendar_events WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM course_schedule WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM grading_weights WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM ta_info WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM professor_info WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM required_materials WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM topic_performance WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM files WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM lectures WHERE class_id = ?", (class_id,))
        await db.execute("DELETE FROM classes WHERE id = ?", (class_id,))
        await db.commit()

    if brain_path and os.path.exists(brain_path):
        try:
            os.remove(brain_path)
            brain_dir = os.path.dirname(brain_path)
            if os.path.isdir(brain_dir) and not os.listdir(brain_dir):
                os.rmdir(brain_dir)
        except OSError:
            pass


@router.patch("/classes/{class_id}/archive")
async def toggle_archive(class_id: str, request: Request) -> dict:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT is_archived FROM classes WHERE id = ?", (class_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Class not found")
        new_state = 0 if row["is_archived"] else 1
        await db.execute(
            "UPDATE classes SET is_archived = ? WHERE id = ?", (new_state, class_id)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        row = await cursor.fetchone()

    return dict(row)
