"""
Semantic and keyword search routes for a class's ingested documents.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db.schema import get_db
from rag.retriever import retrieve_chunks, retrieve_exam_flagged

router = APIRouter(tags=["search"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    filter_type: str | None = None  # "semantic" | "keyword" | "exam-flagged" | None


class SearchResult(BaseModel):
    source_name: str
    excerpt: str
    file_type: str
    relevance_score: float


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/classes/{class_id}/search")
async def search_class(
    class_id: str, body: SearchRequest, request: Request
) -> dict[str, Any]:
    db_path: str = request.app.state.db_path
    app_data: str = request.app.state.app_data
    openai_client = getattr(request.app.state, "openai_client", None)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id FROM classes WHERE id = ?", (class_id,))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Class not found")

    openai_api_key: str | None = None
    if openai_client is not None:
        try:
            openai_api_key = openai_client.api_key  # type: ignore[attr-defined]
        except AttributeError:
            pass

    filter_type = (body.filter_type or "").lower()

    if filter_type == "keyword" or body.query.startswith("#"):
        results = await _keyword_search(db_path, class_id, body.query.lstrip("#").strip())
    elif filter_type == "exam-flagged":
        raw_chunks = retrieve_exam_flagged(
            app_data, class_id, body.query, n_results=10, openai_api_key=openai_api_key
        )
        results = _chunks_to_results(raw_chunks)
    else:
        # Default: semantic search
        raw_chunks = retrieve_chunks(
            app_data,
            class_id,
            body.query,
            n_results=8,
            openai_api_key=openai_api_key,
        )
        results = _chunks_to_results(raw_chunks)

    return {"results": results}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _keyword_search(
    db_path: str, class_id: str, query: str
) -> list[dict[str, Any]]:
    """Simple SQLite LIKE search over processed_reference_path content (stored Markdown)."""
    results: list[dict[str, Any]] = []

    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT id, original_filename, processed_reference_path, file_type
            FROM files
            WHERE class_id = ? AND processed_reference_path IS NOT NULL
            """,
            (class_id,),
        )
        file_rows = await cursor.fetchall()

    for row in file_rows:
        ref_path: str | None = row["processed_reference_path"]
        if not ref_path:
            continue
        try:
            with open(ref_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            continue

        # Find lines containing the query (case-insensitive)
        query_lower = query.lower()
        matching_lines: list[str] = [
            line for line in content.splitlines() if query_lower in line.lower()
        ]
        if not matching_lines:
            continue

        excerpt = " … ".join(matching_lines[:3])[:500]
        results.append(
            {
                "source_name": row["original_filename"],
                "excerpt": excerpt,
                "file_type": row["file_type"] or "unknown",
                "relevance_score": 1.0,  # keyword match — no vector score
            }
        )

    return results


def _chunks_to_results(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_name": c.get("source_name", ""),
            "excerpt": c.get("text", "")[:500],
            "file_type": c.get("file_type", ""),
            "relevance_score": c.get("relevance_score", 0.0),
        }
        for c in chunks
    ]
