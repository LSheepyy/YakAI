"""
YakAI Python sidecar — FastAPI entry point.

Environment variables:
  YAKAI_APP_DATA   Root data directory (set by Tauri on startup, defaults to ~/.yakai)
  YAKAI_PORT       Port to listen on (default: 8765)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db.schema import init_db
from routes import classes, files, health

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
    # openai_client is set here when an API key is configured
    app.state.openai_client = None
    yield


app = FastAPI(
    title="YakAI Sidecar",
    version="0.1.0",
    description="AI study assistant backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "tauri://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(classes.router)
app.include_router(files.router)


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
