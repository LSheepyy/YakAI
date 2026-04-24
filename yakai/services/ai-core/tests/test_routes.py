"""Integration tests for FastAPI routes using TestClient."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# We patch init_db and app state before importing the app
import sys


def _build_test_app(tmp_db_path: str, tmp_app_data: str):
    """Build a fresh FastAPI app wired to a temp database."""
    import importlib
    # Reload to avoid module-level side effects
    import main as m

    # Override state directly via lifespan by manipulating env
    os.environ["YAKAI_APP_DATA"] = tmp_app_data

    # We need to initialise the DB synchronously for the sync TestClient
    import asyncio
    from db.schema import init_db
    asyncio.get_event_loop().run_until_complete(init_db(tmp_db_path))

    # Patch lifespan to inject our test paths
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from routes import classes, files, health
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        app.state.db_path = tmp_db_path
        app.state.app_data = tmp_app_data
        app.state.openai_client = None
        yield

    test_app = FastAPI(lifespan=test_lifespan)
    test_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    test_app.include_router(health.router)
    test_app.include_router(classes.router)
    test_app.include_router(files.router)
    return test_app


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        app = _build_test_app(db_path, tmpdir)
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# ---------------------------------------------------------------------------
# Semesters
# ---------------------------------------------------------------------------

def test_create_semester(client):
    response = client.post("/semesters", json={"name": "Fall 2026", "user_id": "user-1"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fall 2026"
    assert "id" in data


def test_list_semesters_empty(client):
    response = client.get("/semesters")
    assert response.status_code == 200
    assert response.json() == []


def test_list_semesters_with_data(client):
    client.post("/semesters", json={"name": "Fall 2026", "user_id": "user-1"})
    response = client.get("/semesters")
    assert response.status_code == 200
    semesters = response.json()
    assert len(semesters) == 1
    assert semesters[0]["name"] == "Fall 2026"
    assert "classes" in semesters[0]


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

def _create_semester_and_class(client, course_code="ENGR2410", course_name="Circuit Analysis"):
    sem_resp = client.post("/semesters", json={"name": "Fall 2026", "user_id": "user-1"})
    semester_id = sem_resp.json()["id"]
    cls_resp = client.post(
        "/classes",
        json={
            "semester_id": semester_id,
            "course_code": course_code,
            "course_name": course_name,
            "professor": "Dr. Smith",
            "major": "Electrical Engineering",
        },
    )
    return cls_resp


def test_create_class_returns_201(client):
    resp = _create_semester_and_class(client)
    assert resp.status_code == 201


def test_create_class_has_brain_file_path(client):
    resp = _create_semester_and_class(client)
    data = resp.json()
    assert data["brain_file_path"] is not None
    assert data["brain_file_path"].endswith(".md")


def test_create_class_brain_file_exists_on_disk(client):
    resp = _create_semester_and_class(client)
    brain_path = resp.json()["brain_file_path"]
    assert os.path.exists(brain_path)


def test_create_class_brain_file_contains_course_code(client):
    resp = _create_semester_and_class(client, "CS350", "Operating Systems")
    brain_path = resp.json()["brain_file_path"]
    with open(brain_path, encoding="utf-8") as f:
        content = f.read()
    assert "CS350" in content


def test_get_class_returns_detail(client):
    create_resp = _create_semester_and_class(client)
    class_id = create_resp.json()["id"]
    resp = client.get(f"/classes/{class_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == class_id
    assert "professor_info" in data
    assert "grading_weights" in data
    assert "lectures" in data


def test_get_class_404_for_unknown(client):
    resp = client.get("/classes/nonexistent-id")
    assert resp.status_code == 404


def test_archive_class_toggles_state(client):
    create_resp = _create_semester_and_class(client)
    class_id = create_resp.json()["id"]
    assert create_resp.json()["is_archived"] == 0

    archive_resp = client.patch(f"/classes/{class_id}/archive")
    assert archive_resp.status_code == 200
    assert archive_resp.json()["is_archived"] == 1

    unarchive_resp = client.patch(f"/classes/{class_id}/archive")
    assert unarchive_resp.json()["is_archived"] == 0


def test_create_class_auto_generates_slug(client):
    resp = _create_semester_and_class(client, "MATH2210", "Calculus III")
    data = resp.json()
    assert "math2210" in data["slug"]
    assert "calculus" in data["slug"]
