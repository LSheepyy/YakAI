"""
YakAI Python sidecar — FastAPI entry point.

Environment variables:
  YAKAI_APP_DATA   Root data directory (set by Tauri on startup, defaults to ~/.yakai)
  YAKAI_PORT       Port to listen on (default: 8765)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db.schema import get_db, init_db
from routes import chat, classes, files, health, homework, quiz, search, settings

logger = logging.getLogger(__name__)

APP_DATA = os.environ.get("YAKAI_APP_DATA", os.path.join(os.path.expanduser("~"), ".yakai"))
PORT = int(os.environ.get("YAKAI_PORT", "8765"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_dir = os.path.join(APP_DATA, "db")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "yakai.db")
    await init_db(db_path)

    app.state.db_path = db_path
    app.state.app_data = APP_DATA
    app.state.openai_client = None

    # Initialize ChromaDB (PersistentClient) — store app_data so routes can
    # recreate clients as needed (chromadb clients are not async-safe to share
    # across coroutines, so routes call get_chroma_client(app_data) directly).
    app.state.chroma_app_data = APP_DATA
    try:
        from rag.embedder import get_chroma_client

        get_chroma_client(APP_DATA)  # Creates the directory and validates the client
        logger.info("ChromaDB initialized at %s/chroma", APP_DATA)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ChromaDB initialization failed (non-fatal): %s", exc)

    # Restore OpenAI client from persisted key (if any)
    try:
        async with get_db(db_path) as db:
            cursor = await db.execute(
                "SELECT openai_api_key_encrypted FROM users LIMIT 1"
            )
            row = await cursor.fetchone()
            if row and row["openai_api_key_encrypted"]:
                from openai import AsyncOpenAI

                app.state.openai_client = AsyncOpenAI(
                    api_key=row["openai_api_key_encrypted"]
                )
                logger.info("Restored OpenAI client from stored key")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not restore OpenAI key from DB: %s", exc)

    yield


app = FastAPI(
    title="YakAI Sidecar",
    version="0.2.0",
    description="AI study assistant backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "tauri://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routers
app.include_router(health.router)
app.include_router(classes.router)
app.include_router(files.router)

# Phase 2 routers
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(quiz.router)
app.include_router(settings.router)
app.include_router(homework.router)


class ValidateApiKeyRequest(BaseModel):
    api_key: str


@app.post("/validate-api-key")
async def validate_api_key(body: ValidateApiKeyRequest) -> dict:
    """Check that an OpenAI API key can authenticate. Uses a minimal models.list call."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=body.api_key)
        await client.models.list()
        return {"valid": True}
    except Exception:
        return {"valid": False}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=False)
