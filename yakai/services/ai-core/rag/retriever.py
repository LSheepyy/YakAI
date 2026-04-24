"""
RAG retriever — queries ChromaDB collections for relevant text chunks.
"""

from __future__ import annotations

import logging
from typing import Any

from rag.embedder import get_chroma_client, get_collection

logger = logging.getLogger(__name__)

_EXAM_KEYWORDS = {"exam", "midterm", "final", "quiz", "test"}


def retrieve_chunks(
    app_data: str,
    class_id: str,
    query: str,
    n_results: int = 5,
    file_type_filter: str | None = None,
    openai_api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Query ChromaDB for the *n_results* most relevant chunks for *query*.

    Returns a list of dicts with keys:
      text, source_name, file_type, relevance_score, file_id
    """
    try:
        client = get_chroma_client(app_data)
        collection = get_collection(client, class_id, openai_api_key)

        # Bail early if the collection has no documents
        if collection.count() == 0:
            return []

        where: dict[str, Any] | None = None
        if file_type_filter:
            where = {"file_type": file_type_filter}

        kwargs: dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        return _format_results(results)

    except Exception as exc:  # noqa: BLE001
        logger.warning("retrieve_chunks failed for class_id=%s: %s", class_id, exc)
        return []


def retrieve_for_lecture(
    app_data: str,
    class_id: str,
    lecture_id: str,
    query: str,
    n_results: int = 5,
    openai_api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve chunks filtered to those associated with a specific lecture."""
    try:
        client = get_chroma_client(app_data)
        collection = get_collection(client, class_id, openai_api_key)

        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where={"lecture_id": lecture_id},
            include=["documents", "metadatas", "distances"],
        )

        return _format_results(results)

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "retrieve_for_lecture failed for class_id=%s lecture_id=%s: %s",
            class_id,
            lecture_id,
            exc,
        )
        return []


def retrieve_exam_flagged(
    app_data: str,
    class_id: str,
    query: str,
    n_results: int = 10,
    openai_api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve chunks that are semantically relevant AND contain exam-related keywords."""
    # Pull a larger candidate set then filter locally for keywords
    candidates = retrieve_chunks(
        app_data,
        class_id,
        query,
        n_results=n_results * 4,
        openai_api_key=openai_api_key,
    )

    flagged = [
        c for c in candidates
        if any(kw in c["text"].lower() for kw in _EXAM_KEYWORDS)
    ]

    return flagged[:n_results]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_results(results: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten ChromaDB query results into a list of chunk dicts."""
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    chunks: list[dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite.
        # Convert to a 0-1 relevance score.
        relevance = max(0.0, 1.0 - (dist / 2.0))
        chunks.append(
            {
                "text": doc,
                "source_name": meta.get("source_name", ""),
                "file_type": meta.get("file_type", ""),
                "relevance_score": round(relevance, 4),
                "file_id": meta.get("file_id", ""),
            }
        )

    return chunks
