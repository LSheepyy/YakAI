"""
Quiz routes — generate quiz sessions, submit answers, and view topic performance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from chat.engine import log_api_usage
from db.schema import get_db
from quiz.generator import generate_quiz_questions, grade_answer
from rag.retriever import retrieve_chunks, retrieve_for_lecture

router = APIRouter(tags=["quiz"])

_NO_KEY_MSG = "OpenAI API key not configured. Add your key in Settings."

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class GenerateQuizRequest(BaseModel):
    scope: str  # "lecture" | "full" | "weak-areas" | "range"
    num_questions: int = 10
    lecture_id: str | None = None


class SubmitAttemptRequest(BaseModel):
    question_id: str
    user_answer: str
    hints_used: int = 0
    time_taken_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/classes/{class_id}/quiz/generate")
async def generate_quiz(
    class_id: str, body: GenerateQuizRequest, request: Request
) -> dict[str, Any]:
    db_path: str = request.app.state.db_path
    app_data: str = request.app.state.app_data
    openai_client = getattr(request.app.state, "openai_client", None)

    if openai_client is None:
        raise HTTPException(status_code=400, detail=_NO_KEY_MSG)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Class not found")

        # Grading weights for biased question distribution
        cursor = await db.execute(
            "SELECT component, weight_pct FROM grading_weights WHERE class_id = ?",
            (class_id,),
        )
        grading_weights = [dict(r) for r in await cursor.fetchall()]

    openai_api_key: str | None = None
    try:
        openai_api_key = openai_client.api_key  # type: ignore[attr-defined]
    except AttributeError:
        pass

    # --- Retrieve context based on scope ---
    context_chunks = await _retrieve_by_scope(
        app_data=app_data,
        db_path=db_path,
        class_id=class_id,
        scope=body.scope,
        lecture_id=body.lecture_id,
        openai_api_key=openai_api_key,
    )

    if not context_chunks:
        raise HTTPException(
            status_code=422,
            detail=(
                "No course material found for this scope. "
                "Upload lecture notes or slides first."
            ),
        )

    # --- Generate questions ---
    questions_data = await generate_quiz_questions(
        openai_client=openai_client,
        context_chunks=context_chunks,
        num_questions=body.num_questions,
        grading_weights=grading_weights,
    )

    if not questions_data:
        raise HTTPException(status_code=500, detail="Quiz generation returned no questions.")

    now = datetime.utcnow().isoformat()
    session_id = str(uuid.uuid4())

    async with get_db(db_path) as db:
        await db.execute(
            "INSERT INTO quiz_sessions (id, class_id, scope, scope_detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, class_id, body.scope, body.lecture_id, now),
        )

        saved_questions: list[dict[str, Any]] = []
        for q in questions_data:
            q_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO quiz_questions
                    (id, session_id, question_text, correct_answer, question_type,
                     hint_level_1, hint_level_2, hint_level_3, topic_tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    q_id,
                    session_id,
                    q.get("question_text", ""),
                    q.get("correct_answer", ""),
                    q.get("question_type", "short-answer"),
                    q.get("hint_level_1"),
                    q.get("hint_level_2"),
                    q.get("hint_level_3"),
                    q.get("topic_tag"),
                ),
            )
            saved_questions.append(
                {
                    "id": q_id,
                    "question_text": q.get("question_text", ""),
                    "question_type": q.get("question_type", "short-answer"),
                    "hint_level_1": q.get("hint_level_1"),
                    "hint_level_2": q.get("hint_level_2"),
                    "hint_level_3": q.get("hint_level_3"),
                    "topic_tag": q.get("topic_tag"),
                }
            )

        await db.commit()

    # Log usage
    try:
        await log_api_usage(db_path, "gpt-4o", 0, 0, "quiz_generate")
    except Exception:  # noqa: BLE001
        pass

    return {"session_id": session_id, "questions": saved_questions}


@router.post("/quiz/sessions/{session_id}/attempt")
async def submit_attempt(
    session_id: str, body: SubmitAttemptRequest, request: Request
) -> dict[str, Any]:
    db_path: str = request.app.state.db_path
    openai_client = getattr(request.app.state, "openai_client", None)

    if openai_client is None:
        raise HTTPException(status_code=400, detail=_NO_KEY_MSG)

    # Fetch question
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT id, question_text, correct_answer, topic_tag, session_id FROM quiz_questions WHERE id = ?",
            (body.question_id,),
        )
        q_row = await cursor.fetchone()
        if q_row is None:
            raise HTTPException(status_code=404, detail="Question not found")

        # Verify the question belongs to this session
        if q_row["session_id"] != session_id:
            raise HTTPException(status_code=400, detail="Question does not belong to this session")

        # Fetch class_id from the session
        cursor = await db.execute(
            "SELECT class_id FROM quiz_sessions WHERE id = ?", (session_id,)
        )
        session_row = await cursor.fetchone()
        if session_row is None:
            raise HTTPException(status_code=404, detail="Session not found")

    class_id: str = session_row["class_id"]
    question_text: str = q_row["question_text"]
    correct_answer: str = q_row["correct_answer"]
    topic_tag: str | None = q_row["topic_tag"]

    # Grade the answer
    is_correct, explanation = await grade_answer(
        openai_client=openai_client,
        question_text=question_text,
        correct_answer=correct_answer,
        user_answer=body.user_answer,
    )

    now = datetime.utcnow().isoformat()
    attempt_id = str(uuid.uuid4())

    async with get_db(db_path) as db:
        # Save attempt
        await db.execute(
            """
            INSERT INTO quiz_attempts
                (id, question_id, user_answer, is_correct, hints_used, time_taken_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                body.question_id,
                body.user_answer,
                int(is_correct),
                body.hints_used,
                body.time_taken_seconds,
                now,
            ),
        )

        # Upsert topic_performance
        if topic_tag:
            await _upsert_topic_performance(db, class_id, topic_tag, is_correct, now)

        await db.commit()

    # Log usage
    try:
        await log_api_usage(db_path, "gpt-4o-mini", 0, 0, "quiz_grade")
    except Exception:  # noqa: BLE001
        pass

    return {
        "attempt_id": attempt_id,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation,
    }


@router.get("/classes/{class_id}/performance")
async def get_performance(class_id: str, request: Request) -> list[dict[str, Any]]:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Class not found")

        cursor = await db.execute(
            """
            SELECT id, class_id, topic_tag, total_attempts, correct_count,
                   accuracy_rate, last_updated
            FROM topic_performance
            WHERE class_id = ?
            ORDER BY accuracy_rate ASC NULLS LAST
            """,
            (class_id,),
        )
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _retrieve_by_scope(
    app_data: str,
    db_path: str,
    class_id: str,
    scope: str,
    lecture_id: str | None,
    openai_api_key: str | None,
) -> list[dict[str, Any]]:
    """Dispatch context retrieval based on quiz scope."""
    if scope == "lecture":
        if not lecture_id:
            raise HTTPException(
                status_code=400,
                detail="lecture_id is required for scope='lecture'",
            )
        return retrieve_for_lecture(
            app_data, class_id, lecture_id,
            query="key concepts and important points",
            n_results=20,
            openai_api_key=openai_api_key,
        )

    if scope == "weak-areas":
        topics = await _get_weak_topics(db_path, class_id)
        if not topics:
            # Fall back to general retrieval
            return retrieve_chunks(
                app_data, class_id,
                "course material key concepts",
                n_results=20,
                openai_api_key=openai_api_key,
            )
        query = "important concepts in: " + ", ".join(topics)
        return retrieve_chunks(
            app_data, class_id, query, n_results=20, openai_api_key=openai_api_key
        )

    # "full" and "range" — broad retrieval
    return retrieve_chunks(
        app_data, class_id,
        "course material key concepts",
        n_results=20,
        openai_api_key=openai_api_key,
    )


async def _get_weak_topics(db_path: str, class_id: str) -> list[str]:
    """Return topic tags with accuracy_rate < 0.7."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT topic_tag FROM topic_performance
            WHERE class_id = ? AND accuracy_rate < 0.7 AND total_attempts > 0
            ORDER BY accuracy_rate ASC
            LIMIT 5
            """,
            (class_id,),
        )
        rows = await cursor.fetchall()
    return [r["topic_tag"] for r in rows if r["topic_tag"]]


async def _upsert_topic_performance(
    db: Any,
    class_id: str,
    topic_tag: str,
    is_correct: bool,
    now: str,
) -> None:
    """Increment counters and recalculate accuracy_rate for a topic."""
    cursor = await db.execute(
        "SELECT id, total_attempts, correct_count FROM topic_performance WHERE class_id = ? AND topic_tag = ?",
        (class_id, topic_tag),
    )
    existing = await cursor.fetchone()

    if existing:
        total = existing["total_attempts"] + 1
        correct = existing["correct_count"] + (1 if is_correct else 0)
        accuracy = correct / total
        await db.execute(
            """
            UPDATE topic_performance
            SET total_attempts = ?, correct_count = ?, accuracy_rate = ?, last_updated = ?
            WHERE id = ?
            """,
            (total, correct, accuracy, now, existing["id"]),
        )
    else:
        perf_id = str(uuid.uuid4())
        total = 1
        correct = 1 if is_correct else 0
        accuracy = float(correct)
        await db.execute(
            """
            INSERT INTO topic_performance
                (id, class_id, topic_tag, total_attempts, correct_count, accuracy_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (perf_id, class_id, topic_tag, total, correct, accuracy, now),
        )
