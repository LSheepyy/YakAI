"""
Duplicate detection for ingested files.

Two signals are checked:
1. SHA-256 hash of the raw file bytes (exact byte-level duplicate)
2. Text fingerprint — SHA-256 of the first 15 non-empty lines joined (catches
   re-exports / reformatted versions of the same document)
"""

from __future__ import annotations

import hashlib

import aiosqlite


def compute_file_hash(file_bytes: bytes) -> str:
    """Return the SHA-256 hex digest of *file_bytes*."""
    return hashlib.sha256(file_bytes).hexdigest()


def compute_text_fingerprint(text: str) -> str:
    """Return a SHA-256 hex digest of the first 15 non-empty lines of *text*."""
    lines = [line for line in text.splitlines() if line.strip()][:15]
    fingerprint_source = "\n".join(lines)
    return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()


async def check_duplicate(
    db: aiosqlite.Connection,
    class_id: str,
    file_hash: str,
    text_fingerprint: str,
) -> dict | None:
    """Return the existing file record if a duplicate is found, else ``None``.

    A match is detected when either the SHA-256 hash **or** the text
    fingerprint matches an existing file in the same class.
    """
    cursor = await db.execute(
        """
        SELECT id, class_id, original_filename, stored_path,
               processed_reference_path, file_type, sha256_hash,
               text_fingerprint, processed_at, created_at
        FROM files
        WHERE class_id = ?
          AND (sha256_hash = ? OR text_fingerprint = ?)
        LIMIT 1
        """,
        (class_id, file_hash, text_fingerprint),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)
