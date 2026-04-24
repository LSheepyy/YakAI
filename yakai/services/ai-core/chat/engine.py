"""
Chat engine — GPT-4o powered class-scoped Q&A with RAG context injection.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are YakAI, an AI study assistant for a specific college course.
Your ONLY knowledge source is the context provided below — do NOT draw on
outside knowledge, training data, or general internet facts.

Hard constraints:
- If the answer is not in the provided context, say:
  "I don't have enough course material to answer that yet. Try uploading your
  notes or slides for this topic."
- NEVER guess, hallucinate, or extrapolate beyond what the context explicitly
  states.
- NEVER invent formulas, values, or dates.
- Always cite the source document name when referencing specific content.
- Be concise but complete — show full working for math problems.
- If a question is ambiguous, ask for clarification.

Course context:
{context}
"""


# ---------------------------------------------------------------------------
# Core response function
# ---------------------------------------------------------------------------

async def generate_chat_response(
    openai_client: Any,
    class_id: str,
    user_message: str,
    context_chunks: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> tuple[str, list[str]]:
    """Call GPT-4o with RAG context and return (assistant_message, sources).

    *history* is a list of {role, content} dicts (most-recent-last).
    *sources* is a deduplicated list of source_name strings from the chunks.
    """
    # Build context block from retrieved chunks
    if context_chunks:
        context_parts: list[str] = []
        for chunk in context_chunks:
            source = chunk.get("source_name", "Unknown source")
            text = chunk.get("text", "")
            context_parts.append(f"[{source}]\n{text}")
        context_text = "\n\n---\n\n".join(context_parts)
    else:
        context_text = "(No course material available for this query.)"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context_text)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Include conversation history (cap at last 10 turns to manage tokens)
    for turn in history[-10:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": user_message})

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2,
        max_tokens=1500,
    )

    assistant_message: str = response.choices[0].message.content or ""
    tokens_in: int = response.usage.prompt_tokens if response.usage else 0
    tokens_out: int = response.usage.completion_tokens if response.usage else 0

    logger.info(
        "generate_chat_response: tokens_in=%d tokens_out=%d class_id=%s",
        tokens_in,
        tokens_out,
        class_id,
    )

    # Deduplicated sources list
    seen: set[str] = set()
    sources: list[str] = []
    for chunk in context_chunks:
        name = chunk.get("source_name", "")
        if name and name not in seen:
            seen.add(name)
            sources.append(name)

    return assistant_message, sources


# ---------------------------------------------------------------------------
# API usage logging
# ---------------------------------------------------------------------------

# Model pricing per 1M tokens (input / output) in USD — approximate
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "text-embedding-3-small": (0.02, 0.0),
}


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pricing = _MODEL_PRICING.get(model, (10.0, 30.0))
    cost = (tokens_in / 1_000_000) * pricing[0] + (tokens_out / 1_000_000) * pricing[1]
    return round(cost, 8)


async def log_api_usage(
    db_path: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    feature: str,
) -> None:
    """Insert a row into api_usage_log."""
    estimated_cost = _estimate_cost(model, tokens_in, tokens_out)
    now = datetime.utcnow().isoformat()
    log_id = str(uuid.uuid4())

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                INSERT INTO api_usage_log
                    (id, model, tokens_in, tokens_out, estimated_cost_usd, feature, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (log_id, model, tokens_in, tokens_out, estimated_cost, feature, now),
            )
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("log_api_usage failed: %s", exc)
