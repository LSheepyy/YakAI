"""
Homework help route — answers questions using RAG + GPT-4o.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from chat.engine import SYSTEM_PROMPT_TEMPLATE, log_api_usage
from db.schema import get_db
from rag.retriever import retrieve_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["homework"])

_NO_KEY_MSG = "OpenAI API key not configured. Add your key in Settings."

_HOMEWORK_SYSTEM_PROMPT = """\
You are YakAI, an expert study assistant helping a student with homework.
Use ONLY the course material provided in the context below.  Do NOT use
outside knowledge.

Rules:
- Show all working steps for math or derivations.
- If the answer is not found in the context, set sufficient_knowledge to false
  in your response and explain what is missing.
- Be thorough — partial answers are not acceptable.
- Cite the source document when referencing specific content.
- Return a JSON object with these keys:
    "answer": "your full answer here",
    "sufficient_knowledge": true | false

Course context:
{context}
"""


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class HomeworkRequest(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/classes/{class_id}/homework")
async def homework_help(
    class_id: str, body: HomeworkRequest, request: Request
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
        body.question,
        n_results=8,
        openai_api_key=openai_api_key,
    )

    sufficient_knowledge = len(context_chunks) > 0

    if context_chunks:
        context_parts: list[str] = []
        for chunk in context_chunks:
            source = chunk.get("source_name", "Unknown source")
            text = chunk.get("text", "")
            context_parts.append(f"[{source}]\n{text}")
        context_text = "\n\n---\n\n".join(context_parts)
    else:
        context_text = "(No relevant course material found for this question.)"

    system_prompt = _HOMEWORK_SYSTEM_PROMPT.format(context=context_text)

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": body.question},
        ],
        temperature=0.1,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    import json

    raw: str = response.choices[0].message.content or "{}"
    try:
        result = json.loads(raw)
        answer: str = result.get("answer", "")
        sufficient_knowledge = result.get("sufficient_knowledge", sufficient_knowledge)
    except (json.JSONDecodeError, ValueError):
        logger.warning("homework_help: could not parse GPT JSON response")
        answer = raw
        sufficient_knowledge = len(context_chunks) > 0

    # Deduplicated sources
    seen: set[str] = set()
    sources: list[str] = []
    for chunk in context_chunks:
        name = chunk.get("source_name", "")
        if name and name not in seen:
            seen.add(name)
            sources.append(name)

    # Log usage
    try:
        await log_api_usage(db_path, "gpt-4o", 0, 0, "homework")
    except Exception:  # noqa: BLE001
        pass

    return {
        "answer": answer,
        "sources": sources,
        "sufficient_knowledge": bool(sufficient_knowledge),
    }
