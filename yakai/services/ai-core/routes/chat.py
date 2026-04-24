"""
Chat routes — class-scoped conversational Q&A backed by RAG + GPT-4o.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from chat.engine import generate_chat_response, log_api_usage
from db.schema import get_db
from rag.retriever import retrieve_chunks

router = APIRouter(tags=["chat"])

_NO_KEY_MSG = "OpenAI API key not configured. Add your key in Settings."


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    content: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_sources(sources: list[str]) -> str:
    if not sources:
        return ""
    bullet_list = "\n".join(f"- {s}" for s in sources)
    return f"\n\n**Sources:**\n{bullet_list}"


async def _get_history(db_path: str, class_id: str, limit: int = 20) -> list[dict[str, str]]:
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE class_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (class_id, limit),
        )
        rows = await cursor.fetchall()
    # Rows are newest-first; reverse for chronological order
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/classes/{class_id}/chat/messages")
async def list_messages(class_id: str, request: Request) -> list[dict[str, Any]]:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT id FROM classes WHERE id = ?", (class_id,)
        )
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Class not found")

        cursor = await db.execute(
            """
            SELECT id, class_id, role, content, created_at
            FROM chat_messages
            WHERE class_id = ?
            ORDER BY created_at ASC
            """,
            (class_id,),
        )
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]


@router.post("/classes/{class_id}/chat/messages")
async def send_message(
    class_id: str, body: SendMessageRequest, request: Request
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

    openai_api_key: str | None = None
    try:
        openai_api_key = openai_client.api_key  # type: ignore[attr-defined]
    except AttributeError:
        pass

    # Retrieve relevant context
    context_chunks = retrieve_chunks(
        app_data,
        class_id,
        body.content,
        n_results=6,
        openai_api_key=openai_api_key,
    )

    # Load recent history
    history = await _get_history(db_path, class_id)

    # Generate response
    assistant_message, sources = await generate_chat_response(
        openai_client=openai_client,
        class_id=class_id,
        user_message=body.content,
        context_chunks=context_chunks,
        history=history,
    )

    # Append sources as a formatted block
    full_content = assistant_message + _format_sources(sources)

    now = datetime.utcnow().isoformat()
    user_msg_id = str(uuid.uuid4())
    asst_msg_id = str(uuid.uuid4())

    async with get_db(db_path) as db:
        # Save user message
        await db.execute(
            "INSERT INTO chat_messages (id, class_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_msg_id, class_id, "user", body.content, now),
        )
        # Save assistant message
        await db.execute(
            "INSERT INTO chat_messages (id, class_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (asst_msg_id, class_id, "assistant", full_content, now),
        )
        await db.commit()

    # Log usage (fire and forget — don't block response on logging failure)
    try:
        await log_api_usage(db_path, "gpt-4o", 0, 0, "chat")
    except Exception:  # noqa: BLE001
        pass

    return {
        "id": asst_msg_id,
        "class_id": class_id,
        "role": "assistant",
        "content": full_content,
        "created_at": now,
        "sources": sources,
    }


@router.delete("/classes/{class_id}/chat/messages", status_code=204, response_model=None)
async def clear_messages(class_id: str, request: Request) -> None:
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Class not found")

        await db.execute("DELETE FROM chat_messages WHERE class_id = ?", (class_id,))
        await db.commit()
