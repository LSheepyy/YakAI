"""
Database schema initialization and connection management for YakAI.

All IDs are TEXT (UUID4 strings). Timestamps are ISO-8601 strings via
datetime.utcnow().isoformat().
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_CREATE_STATEMENTS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id                      TEXT PRIMARY KEY,
        name                    TEXT NOT NULL,
        email                   TEXT NOT NULL UNIQUE,
        major                   TEXT,
        openai_api_key_encrypted TEXT,
        whisper_model           TEXT NOT NULL DEFAULT 'small',
        last_backup_at          TEXT,
        created_at              TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS semesters (
        id      TEXT PRIMARY KEY,
        name    TEXT NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS classes (
        id                    TEXT PRIMARY KEY,
        semester_id           TEXT NOT NULL REFERENCES semesters(id),
        course_code           TEXT NOT NULL,
        course_name           TEXT NOT NULL,
        slug                  TEXT NOT NULL,
        professor             TEXT,
        major                 TEXT,
        brain_file_path       TEXT,
        inherited_from_class_id TEXT,
        is_archived           INTEGER NOT NULL DEFAULT 0,
        created_at            TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lectures (
        id                  TEXT PRIMARY KEY,
        class_id            TEXT NOT NULL REFERENCES classes(id),
        number              INTEGER,
        date                TEXT,
        title               TEXT,
        transcript_path     TEXT,
        reference_file_path TEXT,
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS files (
        id                      TEXT PRIMARY KEY,
        class_id                TEXT NOT NULL REFERENCES classes(id),
        lecture_id              TEXT REFERENCES lectures(id),
        original_filename       TEXT NOT NULL,
        stored_path             TEXT,
        processed_reference_path TEXT,
        file_type               TEXT,
        sha256_hash             TEXT,
        text_fingerprint        TEXT,
        processed_at            TEXT,
        created_at              TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_sessions (
        id           TEXT PRIMARY KEY,
        class_id     TEXT NOT NULL REFERENCES classes(id),
        scope        TEXT,
        scope_detail TEXT,
        created_at   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id                TEXT PRIMARY KEY,
        session_id        TEXT NOT NULL REFERENCES quiz_sessions(id),
        question_text     TEXT NOT NULL,
        correct_answer    TEXT NOT NULL,
        question_type     TEXT,
        hint_level_1      TEXT,
        hint_level_2      TEXT,
        hint_level_3      TEXT,
        source_lecture_id TEXT REFERENCES lectures(id),
        source_file_id    TEXT REFERENCES files(id),
        topic_tag         TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id                  TEXT PRIMARY KEY,
        question_id         TEXT NOT NULL REFERENCES quiz_questions(id),
        user_answer         TEXT,
        is_correct          INTEGER,
        hints_used          INTEGER NOT NULL DEFAULT 0,
        time_taken_seconds  REAL,
        created_at          TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS topic_performance (
        id             TEXT PRIMARY KEY,
        class_id       TEXT NOT NULL REFERENCES classes(id),
        topic_tag      TEXT NOT NULL,
        total_attempts INTEGER NOT NULL DEFAULT 0,
        correct_count  INTEGER NOT NULL DEFAULT 0,
        accuracy_rate  REAL,
        last_updated   TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id         TEXT PRIMARY KEY,
        class_id   TEXT NOT NULL REFERENCES classes(id),
        role       TEXT NOT NULL,
        content    TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS calendar_events (
        id             TEXT PRIMARY KEY,
        class_id       TEXT NOT NULL REFERENCES classes(id),
        title          TEXT NOT NULL,
        event_date     TEXT,
        event_type     TEXT,
        location       TEXT,
        notes          TEXT,
        source_file_id TEXT REFERENCES files(id),
        created_at     TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS youtube_refs (
        id                      TEXT PRIMARY KEY,
        class_id                TEXT NOT NULL REFERENCES classes(id),
        url                     TEXT NOT NULL,
        title                   TEXT,
        processed_reference_path TEXT,
        created_at              TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS api_usage_log (
        id                TEXT PRIMARY KEY,
        model             TEXT,
        tokens_in         INTEGER,
        tokens_out        INTEGER,
        estimated_cost_usd REAL,
        feature           TEXT,
        created_at        TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS professor_info (
        id              TEXT PRIMARY KEY,
        class_id        TEXT NOT NULL REFERENCES classes(id),
        name            TEXT,
        email           TEXT,
        phone           TEXT,
        office_location TEXT,
        office_hours    TEXT,
        department      TEXT,
        source_file_id  TEXT REFERENCES files(id),
        created_at      TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ta_info (
        id             TEXT PRIMARY KEY,
        class_id       TEXT NOT NULL REFERENCES classes(id),
        name           TEXT,
        email          TEXT,
        office_hours   TEXT,
        source_file_id TEXT REFERENCES files(id),
        created_at     TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS grading_weights (
        id             TEXT PRIMARY KEY,
        class_id       TEXT NOT NULL REFERENCES classes(id),
        component      TEXT NOT NULL,
        weight_pct     REAL,
        source_file_id TEXT REFERENCES files(id),
        created_at     TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS required_materials (
        id               TEXT PRIMARY KEY,
        class_id         TEXT NOT NULL REFERENCES classes(id),
        material_type    TEXT,
        title            TEXT,
        author           TEXT,
        edition          TEXT,
        isbn             TEXT,
        notes            TEXT,
        added_to_class   INTEGER NOT NULL DEFAULT 0,
        source_file_id   TEXT REFERENCES files(id),
        created_at       TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS course_schedule (
        id                TEXT PRIMARY KEY,
        class_id          TEXT NOT NULL REFERENCES classes(id),
        week_number       INTEGER,
        scheduled_date    TEXT,
        topic             TEXT,
        chapters          TEXT,
        linked_lecture_id TEXT REFERENCES lectures(id),
        source_file_id    TEXT REFERENCES files(id),
        created_at        TEXT NOT NULL
    )
    """,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def init_db(db_path: str) -> None:
    """Create all tables in the SQLite database at *db_path*."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        for stmt in _CREATE_STATEMENTS:
            await db.execute(stmt)
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager yielding a configured :class:`aiosqlite.Connection`."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # FK enforcement is enabled per-route when all referenced rows exist.
        # Phase 1 omits user CRUD, so FK on semesters.user_id would fail.
        yield db
