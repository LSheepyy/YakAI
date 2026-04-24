"""Tests for ingestor/duplicate.py"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from ingestor.duplicate import (
    check_duplicate,
    compute_file_hash,
    compute_text_fingerprint,
)


# ---------------------------------------------------------------------------
# Unit tests — pure functions
# ---------------------------------------------------------------------------

def test_compute_file_hash_consistent():
    data = b"hello world"
    assert compute_file_hash(data) == compute_file_hash(data)


def test_compute_file_hash_differs_for_different_bytes():
    assert compute_file_hash(b"abc") != compute_file_hash(b"xyz")


def test_compute_file_hash_is_64_chars():
    h = compute_file_hash(b"test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_text_fingerprint_consistent():
    text = "line one\nline two\nline three"
    assert compute_text_fingerprint(text) == compute_text_fingerprint(text)


def test_compute_text_fingerprint_differs_for_different_text():
    assert compute_text_fingerprint("hello\nworld") != compute_text_fingerprint("foo\nbar")


def test_compute_text_fingerprint_ignores_blank_lines():
    text_with_blanks = "\n\nline one\n\nline two\n"
    text_no_blanks = "line one\nline two"
    # Both should produce the same fingerprint since blanks are filtered
    assert compute_text_fingerprint(text_with_blanks) == compute_text_fingerprint(text_no_blanks)


def test_compute_text_fingerprint_uses_first_15_lines():
    # 20 unique lines — fingerprint must be same for first 15 identical lines
    lines_a = [f"line {i}" for i in range(20)]
    lines_b = [f"line {i}" for i in range(15)] + [f"different {i}" for i in range(5)]
    assert compute_text_fingerprint("\n".join(lines_a)) == compute_text_fingerprint("\n".join(lines_b))


# ---------------------------------------------------------------------------
# Async DB tests
# ---------------------------------------------------------------------------

async def _insert_file(db, class_id: str, file_hash: str, text_fp: str) -> str:
    file_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        INSERT INTO files
            (id, class_id, original_filename, file_type, sha256_hash,
             text_fingerprint, created_at)
        VALUES (?, ?, 'test.pdf', 'pdf', ?, ?, ?)
        """,
        (file_id, class_id, file_hash, text_fp, now),
    )
    await db.commit()
    return file_id


async def _insert_class(db) -> str:
    semester_id = str(uuid.uuid4())
    class_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    await db.execute(
        "INSERT INTO semesters (id, name, user_id) VALUES (?, 'Fall 2026', 'user1')",
        (semester_id,),
    )
    await db.execute(
        """
        INSERT INTO classes
            (id, semester_id, course_code, course_name, slug, created_at)
        VALUES (?, ?, 'TEST101', 'Test Course', 'test101-test-course', ?)
        """,
        (class_id, semester_id, now),
    )
    await db.commit()
    return class_id


@pytest.mark.asyncio
async def test_check_duplicate_returns_none_when_no_match(temp_db):
    class_id = await _insert_class(temp_db)
    result = await check_duplicate(temp_db, class_id, "aabbcc", "ddeeff")
    assert result is None


@pytest.mark.asyncio
async def test_check_duplicate_finds_by_hash(temp_db):
    class_id = await _insert_class(temp_db)
    file_hash = "abc123"
    text_fp = "fp001"
    inserted_id = await _insert_file(temp_db, class_id, file_hash, text_fp)

    result = await check_duplicate(temp_db, class_id, file_hash, "completely-different-fp")
    assert result is not None
    assert result["id"] == inserted_id


@pytest.mark.asyncio
async def test_check_duplicate_finds_by_fingerprint(temp_db):
    class_id = await _insert_class(temp_db)
    file_hash = "hashXXX"
    text_fp = "fpYYY"
    inserted_id = await _insert_file(temp_db, class_id, file_hash, text_fp)

    result = await check_duplicate(temp_db, class_id, "completely-different-hash", text_fp)
    assert result is not None
    assert result["id"] == inserted_id


@pytest.mark.asyncio
async def test_check_duplicate_no_cross_class_match(temp_db):
    """A duplicate in class A should not be reported for class B."""
    class_a = await _insert_class(temp_db)
    # Create second class
    semester_id = str(uuid.uuid4())
    class_b = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    await temp_db.execute(
        "INSERT INTO semesters (id, name, user_id) VALUES (?, 'Spring 2026', 'user1')",
        (semester_id,),
    )
    await temp_db.execute(
        """
        INSERT INTO classes
            (id, semester_id, course_code, course_name, slug, created_at)
        VALUES (?, ?, 'OTHER202', 'Other Course', 'other202-other-course', ?)
        """,
        (class_b, semester_id, now),
    )
    await temp_db.commit()

    file_hash = "shared_hash"
    text_fp = "shared_fp"
    await _insert_file(temp_db, class_a, file_hash, text_fp)

    # Should not find in class_b
    result = await check_duplicate(temp_db, class_b, file_hash, text_fp)
    assert result is None
