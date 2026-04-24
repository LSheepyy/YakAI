"""
PDF content extraction and classification for YakAI.

Depends on PyMuPDF (imported as ``fitz``). Image analysis uses GPT-4o vision
when an OpenAI client is provided; otherwise it degrades gracefully.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_pdf_content(file_bytes: bytes) -> dict[str, Any]:
    """Extract text, images, and metadata from a PDF.

    Returns a dict with keys:
    - ``text``: full plain-text content (str)
    - ``images``: list of raw image bytes (list[bytes])
    - ``page_count``: number of pages (int)
    - ``first_lines``: first 10 non-empty text lines (list[str])
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text: list[str] = []
    images: list[bytes] = []

    for page in doc:
        pages_text.append(page.get_text())
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            images.append(base_image["image"])

    full_text = "\n".join(pages_text)
    first_lines = [line for line in full_text.splitlines() if line.strip()][:10]

    return {
        "text": full_text,
        "images": images,
        "page_count": len(doc),
        "first_lines": first_lines,
    }


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

_SYLLABUS_KEYWORDS: frozenset[str] = frozenset(
    ["syllabus", "course outline", "grading", "office hours", "week"]
)
_HOMEWORK_KEYWORDS: frozenset[str] = frozenset(
    ["assignment", "due date", "due:", "points", "submit"]
)


def classify_pdf(text: str) -> str:
    """Classify a PDF document by its text content.

    Returns one of ``"syllabus"``, ``"homework"``, or ``"notes"``.
    """
    lower = text.lower()

    syllabus_hits = sum(1 for kw in _SYLLABUS_KEYWORDS if kw in lower)
    homework_hits = sum(1 for kw in _HOMEWORK_KEYWORDS if kw in lower)

    if syllabus_hits >= 3:
        return "syllabus"
    if homework_hits >= 2:
        return "homework"
    return "notes"


# ---------------------------------------------------------------------------
# Image analysis
# ---------------------------------------------------------------------------

async def analyze_images_with_gpt4o(
    images: list[bytes],
    openai_client: Any,
    class_context: str = "",
) -> list[str]:
    """Describe each image using GPT-4o vision.

    Returns a list of description strings, one per image.
    If *openai_client* is ``None`` (e.g. in tests), returns an empty list.
    """
    if openai_client is None or not images:
        return []

    descriptions: list[str] = []
    context_note = f" This image is from a {class_context} course." if class_context else ""

    for img_bytes in images:
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        # Detect a basic MIME type from magic bytes
        mime = _detect_image_mime(img_bytes)
        data_url = f"data:{mime};base64,{encoded}"

        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Describe the content of this image concisely, "
                                f"focusing on any diagrams, equations, or charts.{context_note}"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            max_tokens=300,
        )
        descriptions.append(response.choices[0].message.content or "")

    return descriptions


def _detect_image_mime(img_bytes: bytes) -> str:
    """Return a best-guess MIME type from the first bytes of an image."""
    if img_bytes[:4] == b"\x89PNG":
        return "image/png"
    if img_bytes[:2] == b"\xff\xd8":
        return "image/jpeg"
    if img_bytes[:4] in (b"GIF8", b"GIF9"):
        return "image/gif"
    return "image/png"  # safe default for PDF-extracted images
