"""Shared pytest fixtures for YakAI sidecar tests."""

from __future__ import annotations

import os
import tempfile

import aiosqlite
import pytest
import pytest_asyncio

from db.schema import init_db


@pytest_asyncio.fixture
async def temp_db():
    """Yield an initialised aiosqlite connection backed by a temp file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        await init_db(db_path)
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db


@pytest.fixture
def temp_dir():
    """Yield a temporary directory path that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
