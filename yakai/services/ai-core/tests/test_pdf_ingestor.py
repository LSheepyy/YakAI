"""Tests for ingestor/pdf.py"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ingestor.pdf import (
    analyze_images_with_gpt4o,
    classify_pdf,
    extract_pdf_content,
)


# ---------------------------------------------------------------------------
# classify_pdf
# ---------------------------------------------------------------------------

def test_classify_syllabus():
    text = """
    Course Syllabus — ENGR2410 Circuit Analysis
    Office Hours: Tue/Thu 2–4pm, ENG 214
    Grading: Midterm 30%, Final 40%, Assignments 20%, Quizzes 10%
    Week 1: Introduction to KVL
    Week 2: KCL and Mesh Analysis
    """
    assert classify_pdf(text) == "syllabus"


def test_classify_homework():
    text = """
    Assignment 1 — Due: September 15
    1. Solve the circuit shown below. (10 points)
    2. Calculate the Thevenin equivalent. (10 points)
    Submit via the course portal by midnight.
    """
    assert classify_pdf(text) == "homework"


def test_classify_notes_default():
    text = """
    Lecture notes for today's class.
    We covered the basics of nodal analysis.
    The professor drew a diagram on the board.
    """
    assert classify_pdf(text) == "notes"


def test_classify_prefers_syllabus_over_homework_when_both_signals_present():
    # Strong syllabus signal should win
    text = """
    Syllabus — Course Outline
    Office Hours: Mon/Wed 3–5pm
    Grading Breakdown: Week 1 topics
    Assignment due date: September 10
    """
    result = classify_pdf(text)
    assert result == "syllabus"


def test_classify_case_insensitive():
    text = "SYLLABUS — OFFICE HOURS — GRADING — COURSE OUTLINE — WEEK 1"
    assert classify_pdf(text) == "syllabus"


# ---------------------------------------------------------------------------
# extract_pdf_content (mocked fitz)
# ---------------------------------------------------------------------------

def _make_mock_page(text: str = "Sample text\nSecond line", images=None):
    page = MagicMock()
    page.get_text.return_value = text
    page.get_images.return_value = images or []
    return page


def _make_mock_doc(pages=None):
    doc = MagicMock()
    pages = pages or [_make_mock_page()]
    doc.__iter__ = MagicMock(return_value=iter(pages))
    doc.__len__ = MagicMock(return_value=len(pages))
    return doc


def test_extract_pdf_content_returns_text():
    mock_doc = _make_mock_doc([_make_mock_page("Hello PDF\nSecond line")])
    with patch("ingestor.pdf.fitz.open", return_value=mock_doc):
        result = extract_pdf_content(b"fake-pdf-bytes")

    assert "Hello PDF" in result["text"]
    assert result["page_count"] == 1
    assert "Hello PDF" in result["first_lines"]


def test_extract_pdf_content_multi_page():
    pages = [
        _make_mock_page("Page 1 content"),
        _make_mock_page("Page 2 content"),
        _make_mock_page("Page 3 content"),
    ]
    mock_doc = _make_mock_doc(pages)
    with patch("ingestor.pdf.fitz.open", return_value=mock_doc):
        result = extract_pdf_content(b"fake")

    assert result["page_count"] == 3
    assert "Page 1 content" in result["text"]
    assert "Page 3 content" in result["text"]


def test_extract_pdf_content_extracts_images():
    img_info = [(1, None, None, None, None, None, None, None, None)]  # xref = 1
    page = _make_mock_page(images=img_info)
    mock_doc = _make_mock_doc([page])
    mock_doc.extract_image.return_value = {"image": b"\x89PNG fake image bytes"}

    with patch("ingestor.pdf.fitz.open", return_value=mock_doc):
        result = extract_pdf_content(b"fake")

    assert len(result["images"]) == 1
    assert result["images"][0] == b"\x89PNG fake image bytes"


def test_extract_pdf_content_first_lines_capped_at_10():
    long_text = "\n".join(f"Line {i}" for i in range(30))
    mock_doc = _make_mock_doc([_make_mock_page(long_text)])
    with patch("ingestor.pdf.fitz.open", return_value=mock_doc):
        result = extract_pdf_content(b"fake")

    assert len(result["first_lines"]) == 10


# ---------------------------------------------------------------------------
# analyze_images_with_gpt4o
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_images_returns_empty_when_client_is_none():
    result = await analyze_images_with_gpt4o([b"fake image"], openai_client=None)
    assert result == []


@pytest.mark.asyncio
async def test_analyze_images_returns_empty_for_empty_list():
    mock_client = MagicMock()
    result = await analyze_images_with_gpt4o([], openai_client=mock_client)
    assert result == []


@pytest.mark.asyncio
async def test_analyze_images_calls_gpt4o_once_per_image():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "A circuit diagram"
    mock_client.chat.completions.create = MagicMock(
        return_value=mock_response
    )

    # Patch to make it synchronous for this mock
    import asyncio

    async def fake_create(**kwargs):
        return mock_response

    mock_client.chat.completions.create = fake_create

    images = [b"\x89PNG img1", b"\xff\xd8 img2"]
    result = await analyze_images_with_gpt4o(images, mock_client)
    assert len(result) == 2
    assert all(r == "A circuit diagram" for r in result)
