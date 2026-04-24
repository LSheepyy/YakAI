"""
RAG embedder — ChromaDB document storage with OpenAI or default embeddings.

When an OpenAI client is available we use text-embedding-3-small (via
chromadb's OpenAIEmbeddingFunction).  When no key is configured we fall
back to chromadb's default sentence-transformers embedding so the app still
works offline — just slower on first use while the model downloads.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import chromadb

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client / collection helpers
# ---------------------------------------------------------------------------

def get_chroma_client(app_data: str) -> chromadb.PersistentClient:
    """Return (or create) a ChromaDB PersistentClient rooted at *app_data*/chroma."""
    chroma_dir = os.path.join(app_data, "chroma")
    os.makedirs(chroma_dir, exist_ok=True)
    return chromadb.PersistentClient(path=chroma_dir)


def get_collection(
    client: chromadb.ClientAPI,
    class_id: str,
    openai_api_key: str | None = None,
) -> chromadb.Collection:
    """Return (or create) the ChromaDB collection for *class_id*.

    If *openai_api_key* is provided the collection uses OpenAI embeddings
    (text-embedding-3-small).  Otherwise it falls back to chromadb's built-in
    sentence-transformers embedding.
    """
    collection_name = f"class_{class_id}"

    embedding_function = _resolve_embedding_function(openai_api_key)

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,  # type: ignore[arg-type]
        metadata={"hnsw:space": "cosine"},
    )


def _resolve_embedding_function(
    openai_api_key: str | None,
) -> Any | None:
    """Build the embedding function, preferring OpenAI when a key is available."""
    if openai_api_key:
        try:
            from chromadb.utils import embedding_functions

            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-3-small",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not create OpenAI embedding function: %s", exc)

    # Fall back to sentence-transformers (chromadb default)
    try:
        from chromadb.utils import embedding_functions

        return embedding_functions.DefaultEmbeddingFunction()
    except ImportError:
        logger.warning(
            "sentence-transformers not installed; ChromaDB will use its "
            "built-in default embedding.  Install sentence-transformers for "
            "better local embeddings."
        )
        return None


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split *text* into overlapping chunks of roughly *chunk_size* characters."""
    if not text or not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Embedding / deletion
# ---------------------------------------------------------------------------

def embed_document(
    app_data: str,
    class_id: str,
    file_id: str,
    file_type: str,
    source_name: str,
    text: str,
    extra_metadata: dict[str, Any] | None = None,
    openai_api_key: str | None = None,
) -> int:
    """Chunk *text* and upsert all chunks into the class ChromaDB collection.

    Returns the number of chunks added.  Existing chunks for *file_id* are
    deleted first so re-ingesting a file is idempotent.
    """
    if not text or not text.strip():
        logger.info("embed_document: empty text for file_id=%s, skipping", file_id)
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    client = get_chroma_client(app_data)
    collection = get_collection(client, class_id, openai_api_key)

    # Remove any previous version of this document
    delete_document(app_data, class_id, file_id, openai_api_key=openai_api_key)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    base_meta: dict[str, Any] = {
        "class_id": class_id,
        "file_id": file_id,
        "file_type": file_type,
        "source_name": source_name,
    }
    if extra_metadata:
        base_meta.update(extra_metadata)

    for idx, chunk in enumerate(chunks):
        chunk_id = f"{file_id}_chunk_{idx}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({**base_meta, "chunk_index": idx})

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    logger.info(
        "embed_document: added %d chunks for file_id=%s in class_id=%s",
        len(chunks),
        file_id,
        class_id,
    )
    return len(chunks)


def delete_document(
    app_data: str,
    class_id: str,
    file_id: str,
    openai_api_key: str | None = None,
) -> None:
    """Remove all ChromaDB chunks associated with *file_id* from the class collection."""
    try:
        client = get_chroma_client(app_data)
        collection = get_collection(client, class_id, openai_api_key)
        collection.delete(where={"file_id": file_id})
        logger.info("delete_document: removed chunks for file_id=%s", file_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("delete_document failed for file_id=%s: %s", file_id, exc)
