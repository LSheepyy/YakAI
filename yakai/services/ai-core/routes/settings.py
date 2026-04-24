"""
Settings routes — API key management and cost summary.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db.schema import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])

# Pricing per 1M tokens (input / output) in USD
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "text-embedding-3-small": (0.02, 0.0),
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SetApiKeyRequest(BaseModel):
    api_key: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/settings/cost-summary")
async def cost_summary(request: Request) -> dict[str, Any]:
    """Aggregate api_usage_log into a cost summary."""
    db_path: str = request.app.state.db_path

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT model, feature, tokens_in, tokens_out, estimated_cost_usd FROM api_usage_log"
        )
        rows = await cursor.fetchall()

    total_cost = 0.0
    by_feature: dict[str, float] = {}
    by_model: dict[str, float] = {}

    for row in rows:
        cost = row["estimated_cost_usd"] or 0.0
        total_cost += cost

        feature = row["feature"] or "unknown"
        by_feature[feature] = round(by_feature.get(feature, 0.0) + cost, 8)

        model = row["model"] or "unknown"
        by_model[model] = round(by_model.get(model, 0.0) + cost, 8)

    return {
        "total_cost": round(total_cost, 6),
        "by_feature": by_feature,
        "by_model": by_model,
    }


@router.post("/settings/api-key")
async def set_api_key(body: SetApiKeyRequest, request: Request) -> dict[str, bool]:
    """Validate an OpenAI API key and store it on app.state.openai_client.

    Also persists the key in the first users row (plain-text, single-user
    desktop app — no encryption needed at this stage).
    """
    api_key = body.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key must not be empty")

    # Validate with OpenAI
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        await client.models.list()
    except Exception as exc:  # noqa: BLE001
        logger.warning("API key validation failed: %s", exc)
        return {"valid": False}

    # Store on app state
    request.app.state.openai_client = client  # type: ignore[assignment]

    # Persist to DB (best-effort — single-user, first users row)
    db_path: str = request.app.state.db_path
    try:
        async with get_db(db_path) as db:
            cursor = await db.execute("SELECT id FROM users LIMIT 1")
            user_row = await cursor.fetchone()
            if user_row:
                await db.execute(
                    "UPDATE users SET openai_api_key_encrypted = ? WHERE id = ?",
                    (api_key, user_row["id"]),
                )
                await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist API key to DB: %s", exc)

    return {"valid": True}
