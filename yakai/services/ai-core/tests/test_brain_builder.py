"""Tests for brain/builder.py"""

from __future__ import annotations

import os

import pytest

from brain.builder import generate_brain_file, update_brain_file, write_brain_file


# ---------------------------------------------------------------------------
# generate_brain_file
# ---------------------------------------------------------------------------

def test_generate_brain_file_contains_course_code():
    info = {"course_code": "ENGR2410", "course_name": "Circuit Analysis", "slug": "engr2410"}
    content = generate_brain_file(info)
    assert "ENGR2410" in content


def test_generate_brain_file_contains_course_name():
    info = {"course_code": "CS101", "course_name": "Intro to CS", "slug": "cs101"}
    content = generate_brain_file(info)
    assert "Intro to CS" in content


def test_generate_brain_file_contains_professor():
    info = {
        "course_code": "MATH201",
        "course_name": "Calculus II",
        "professor": "Dr. Johnson",
        "slug": "math201",
    }
    content = generate_brain_file(info)
    assert "Dr. Johnson" in content


def test_generate_brain_file_has_required_sections():
    info = {"course_code": "X", "course_name": "Y", "slug": "x-y"}
    content = generate_brain_file(info)
    required_sections = [
        "## When to Use This Brain",
        "## ⚠️ Hard Constraints",
        "## Course Topics (Master Index)",
        "## Key Formulas (Class-Approved Only)",
        "## Lecture Index",
        "## Homework",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: {section}"


def test_generate_brain_file_has_yaml_frontmatter():
    info = {"course_code": "PHYS101", "slug": "phys101", "course_name": "Physics"}
    content = generate_brain_file(info)
    assert content.startswith("---")
    assert "course-code: PHYS101" in content


def test_generate_brain_file_minimal_info_no_crash():
    content = generate_brain_file({})
    assert "## When to Use This Brain" in content


def test_generate_brain_file_with_references():
    info = {"course_code": "BIO101", "slug": "bio101", "course_name": "Biology"}
    refs = [
        {"title": "Lecture 01 — Cell Division", "date": "2026-09-08", "reference_file_path": "/path/lec01.md"},
        {"title": "Lecture 02 — Mitosis", "date": "2026-09-10", "reference_file_path": "/path/lec02.md"},
    ]
    content = generate_brain_file(info, references=refs)
    assert "Lecture 01 — Cell Division" in content
    assert "Lecture 02 — Mitosis" in content


def test_generate_brain_file_with_semester_and_major():
    info = {
        "course_code": "EE301",
        "course_name": "Signals",
        "slug": "ee301",
        "semester": "Fall 2026",
        "major": "Electrical Engineering",
    }
    content = generate_brain_file(info)
    assert "Fall 2026" in content
    assert "Electrical Engineering" in content


# ---------------------------------------------------------------------------
# write_brain_file
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_write_brain_file_creates_file(temp_dir):
    path = os.path.join(temp_dir, "subdir", "brain.md")
    await write_brain_file(path, "# Test Brain")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        assert f.read() == "# Test Brain"


@pytest.mark.asyncio
async def test_write_brain_file_overwrites_existing(temp_dir):
    path = os.path.join(temp_dir, "brain.md")
    await write_brain_file(path, "old content")
    await write_brain_file(path, "new content")
    with open(path, encoding="utf-8") as f:
        assert f.read() == "new content"


# ---------------------------------------------------------------------------
# update_brain_file
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_brain_file_appends_to_lecture_index(temp_dir):
    path = os.path.join(temp_dir, "brain.md")
    initial = generate_brain_file({"course_code": "EE", "slug": "ee", "course_name": "EE"})
    await write_brain_file(path, initial)

    await update_brain_file(path, "Lecture Index", "- [Lecture 01 — Intro](references/lec01.md)")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    assert "Lecture 01 — Intro" in content
    assert "Lecture Index" in content


@pytest.mark.asyncio
async def test_update_brain_file_creates_section_if_missing(temp_dir):
    path = os.path.join(temp_dir, "brain.md")
    await write_brain_file(path, "# Brain\n\n## Lecture Index\n")
    await update_brain_file(path, "New Section", "- some new entry")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    assert "New Section" in content
    assert "some new entry" in content
