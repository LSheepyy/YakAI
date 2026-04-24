"""
File ingestion route — handles upload, duplicate detection, PDF processing,
and ChromaDB embedding of extracted text.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import BaseModel

from brain.builder import update_brain_file
from db.schema import get_db
from ingestor.duplicate import check_duplicate, compute_file_hash, compute_text_fingerprint
from ingestor.pdf import classify_pdf, extract_pdf_content
from ingestor.syllabus import extract_syllabus_data, save_syllabus_data

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])

_PDF_EXTS = {".pdf"}
_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}
_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
_SLIDE_EXTS = {".pptx", ".key", ".odp"}

_SUPPORTED_EXTS = _PDF_EXTS | _VIDEO_EXTS | _AUDIO_EXTS | _IMAGE_EXTS | _SLIDE_EXTS


def _detect_type_from_ext(filename: str) -> str | None:
    ext = os.path.splitext(filename.lower())[1]
    if ext in _PDF_EXTS:
        return "pdf"
    if ext in _VIDEO_EXTS:
        return "video"
    if ext in _AUDIO_EXTS:
        return "audio"
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _SLIDE_EXTS:
        return "slides"
    return None


def _get_openai_api_key(request: Request) -> str | None:
    openai_client = getattr(request.app.state, "openai_client", None)
    if openai_client is None:
        return None
    try:
        return openai_client.api_key  # type: ignore[attr-defined]
    except AttributeError:
        return None


def _trigger_embedding(
    app_data: str,
    class_id: str,
    file_id: str,
    file_type: str,
    source_name: str,
    text: str,
    openai_api_key: str | None,
) -> None:
    """Embed *text* into ChromaDB (best-effort, non-fatal on failure)."""
    if not text or not text.strip():
        return
    try:
        from rag.embedder import embed_document

        chunks_added = embed_document(
            app_data=app_data,
            class_id=class_id,
            file_id=file_id,
            file_type=file_type,
            source_name=source_name,
            text=text,
            openai_api_key=openai_api_key,
        )
        logger.info(
            "_trigger_embedding: %d chunks for file_id=%s", chunks_added, file_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("_trigger_embedding failed for file_id=%s: %s", file_id, exc)


async def _update_brain(brain_file_path: str | None, filename: str, file_type: str) -> None:
    """Append a reference line to the BRAIN file (best-effort)."""
    if not brain_file_path:
        return
    try:
        section = "Documents & Slides" if file_type in ("pdf", "notes", "homework") else "Lecture Index"
        entry = f"- {filename} (type: {file_type})"
        await update_brain_file(brain_file_path, section, entry)
    except Exception as exc:  # noqa: BLE001
        logger.warning("_update_brain failed: %s", exc)


@router.post("/classes/{class_id}/ingest")
async def ingest_file(class_id: str, file: UploadFile, request: Request) -> dict[str, Any]:
    db_path: str = request.app.state.db_path
    app_data: str = request.app.state.app_data
    openai_api_key = _get_openai_api_key(request)

    # Verify class exists
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id, slug, brain_file_path FROM classes WHERE id = ?", (class_id,))
        cls_row = await cursor.fetchone()
        if cls_row is None:
            raise HTTPException(status_code=404, detail="Class not found")

    file_bytes = await file.read()
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename.lower())[1]

    if ext not in _SUPPORTED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Supported: PDF, MP4, MOV, MP3, WAV, M4A, JPG, PNG, PPTX, YouTube URLs."
            ),
        )

    file_hash = compute_file_hash(file_bytes)
    text_fp = ""
    file_type = _detect_type_from_ext(filename) or "pdf"
    reference_path: str | None = None
    now = datetime.utcnow().isoformat()
    file_id = str(uuid.uuid4())

    # --- PDF-specific processing ---
    extracted_text = ""
    if file_type == "pdf":
        pdf_data = extract_pdf_content(file_bytes)
        extracted_text = pdf_data["text"]
        text_fp = compute_text_fingerprint(extracted_text)

        # Override type based on content classification
        classified = classify_pdf(extracted_text)
        if classified == "syllabus":
            file_type = "syllabus"
        elif classified == "homework":
            file_type = "homework"

    # --- Duplicate check ---
    async with get_db(db_path) as db:
        existing = await check_duplicate(db, class_id, file_hash, text_fp)
        if existing:
            return {
                "file_id": existing["id"],
                "type": existing["file_type"],
                "duplicate": True,
                "existing": existing,
                "reference_path": existing.get("processed_reference_path"),
            }

    # --- Persist raw file ---
    stored_dir = os.path.join(app_data, "data", cls_row["slug"], "raw")
    os.makedirs(stored_dir, exist_ok=True)
    stored_path = os.path.join(stored_dir, filename)
    with open(stored_path, "wb") as fh:
        fh.write(file_bytes)

    # --- Create reference Markdown for PDFs / syllabus ---
    if file_type in ("pdf", "notes", "syllabus", "homework"):
        ref_dir = os.path.join(app_data, "data", cls_row["slug"], "references")
        os.makedirs(ref_dir, exist_ok=True)
        base = os.path.splitext(filename)[0].lower().replace(" ", "-")
        reference_path = os.path.join(ref_dir, f"{base}.md")
        with open(reference_path, "w", encoding="utf-8") as fh:
            fh.write(f"# {filename}\n\nType: {file_type}\n\n## Extracted Text\n\n{extracted_text[:5000]}\n")

    # --- Persist file record ---
    async with get_db(db_path) as db:
        await db.execute(
            """
            INSERT INTO files
                (id, class_id, lecture_id, original_filename, stored_path,
                 processed_reference_path, file_type, sha256_hash,
                 text_fingerprint, processed_at, created_at)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id, class_id, filename, stored_path,
                reference_path, file_type, file_hash,
                text_fp, now, now,
            ),
        )
        await db.commit()

    # --- Syllabus: extract data and return for user confirmation ---
    if file_type == "syllabus":
        openai_client = getattr(request.app.state, "openai_client", None)
        syllabus_data = await extract_syllabus_data(extracted_text, openai_client)
        # Note: embedding happens after the user confirms (in /syllabus/confirm)
        return {
            "file_id": file_id,
            "type": file_type,
            "duplicate": False,
            "reference_path": reference_path,
            "status": "pending_confirmation",
            "syllabus_data": syllabus_data,
        }

    # --- Embed non-syllabus PDFs immediately ---
    if extracted_text:
        _trigger_embedding(
            app_data=app_data,
            class_id=class_id,
            file_id=file_id,
            file_type=file_type,
            source_name=filename,
            text=extracted_text,
            openai_api_key=openai_api_key,
        )
        await _update_brain(cls_row["brain_file_path"], filename, file_type)

    return {
        "file_id": file_id,
        "type": file_type,
        "duplicate": False,
        "reference_path": reference_path,
    }


# ---------------------------------------------------------------------------
# Syllabus confirmation
# ---------------------------------------------------------------------------

class SyllabusConfirmRequest(BaseModel):
    file_id: str
    syllabus_data: dict


@router.post("/classes/{class_id}/syllabus/confirm")
async def confirm_syllabus(
    class_id: str, body: SyllabusConfirmRequest, request: Request
) -> dict[str, Any]:
    db_path: str = request.app.state.db_path
    app_data: str = request.app.state.app_data
    openai_api_key = _get_openai_api_key(request)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id, brain_file_path FROM classes WHERE id = ?", (class_id,))
        cls_row = await cursor.fetchone()
        if cls_row is None:
            raise HTTPException(status_code=404, detail="Class not found")

        cursor = await db.execute(
            "SELECT id, original_filename, stored_path FROM files WHERE id = ? AND class_id = ?",
            (body.file_id, class_id),
        )
        file_row = await cursor.fetchone()
        if file_row is None:
            raise HTTPException(status_code=404, detail="File not found")

        await save_syllabus_data(db, class_id, body.syllabus_data, body.file_id)

    # Embed the syllabus text now that the user has confirmed
    stored_path: str | None = file_row["stored_path"]
    if stored_path and os.path.exists(stored_path):
        try:
            from ingestor.pdf import extract_pdf_content

            with open(stored_path, "rb") as fh:
                raw_bytes = fh.read()
            pdf_data = extract_pdf_content(raw_bytes)
            extracted_text = pdf_data["text"]
            if extracted_text:
                _trigger_embedding(
                    app_data=app_data,
                    class_id=class_id,
                    file_id=body.file_id,
                    file_type="syllabus",
                    source_name=file_row["original_filename"],
                    text=extracted_text,
                    openai_api_key=openai_api_key,
                )
                await _update_brain(cls_row["brain_file_path"], file_row["original_filename"], "syllabus")
        except Exception as exc:  # noqa: BLE001
            logger.warning("confirm_syllabus: embedding failed (non-fatal): %s", exc)

    return {"status": "saved", "file_id": body.file_id}
