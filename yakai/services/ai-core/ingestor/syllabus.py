"""
Syllabus extraction, storage, and diffing for YakAI.

GPT-4o is used to parse structured data from raw syllabus text.
When openai_client is None (test mode), a safe placeholder dict is returned.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

import aiosqlite


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a precise data extractor. Given the raw text of a university course
syllabus, return ONLY a JSON object — no prose, no markdown fences — with
exactly this structure:

{
  "course": {
    "code": "",
    "name": "",
    "section": "",
    "credits": "",
    "schedule": ""
  },
  "professor": {
    "name": "",
    "email": "",
    "phone": "",
    "office": "",
    "hours": ""
  },
  "tas": [
    {"name": "", "email": "", "hours": ""}
  ],
  "materials": [
    {"type": "", "title": "", "author": "", "edition": "", "isbn": ""}
  ],
  "grading": [
    {"component": "", "weight_pct": 0}
  ],
  "schedule": [
    {"week_or_date": "", "topic": "", "chapters": ""}
  ],
  "events": [
    {"title": "", "date": "", "type": "", "location": ""}
  ],
  "policies": {
    "late": "",
    "attendance": "",
    "integrity": ""
  }
}

Leave a field as an empty string or empty array if the information is not
present. Do not add extra keys.

SYLLABUS TEXT:
"""

_PLACEHOLDER: dict[str, Any] = {
    "course": {"code": "", "name": "", "section": "", "credits": "", "schedule": ""},
    "professor": {"name": "", "email": "", "phone": "", "office": "", "hours": ""},
    "tas": [],
    "materials": [],
    "grading": [],
    "schedule": [],
    "events": [],
    "policies": {"late": "", "attendance": "", "integrity": ""},
}


async def extract_syllabus_data(
    text: str,
    openai_client: Any,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """Extract structured syllabus data from raw text via GPT-4o.

    Returns *_PLACEHOLDER* when *openai_client* is ``None`` (graceful
    degradation for tests and offline use).
    """
    if openai_client is None:
        return _PLACEHOLDER.copy()

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": _EXTRACTION_PROMPT + text,
            }
        ],
        max_tokens=2048,
        temperature=0,
    )
    raw = response.choices[0].message.content or "{}"
    # Strip accidental markdown code fences
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

async def save_syllabus_data(
    db: aiosqlite.Connection,
    class_id: str,
    data: dict[str, Any],
    source_file_id: str,
) -> None:
    """Persist extracted syllabus data into the relevant SQLite tables."""
    now = datetime.utcnow().isoformat()

    # Professor info
    prof = data.get("professor", {})
    if prof.get("name"):
        await db.execute(
            """
            INSERT INTO professor_info
                (id, class_id, name, email, phone, office_location,
                 office_hours, department, source_file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                class_id,
                prof.get("name"),
                prof.get("email"),
                prof.get("phone"),
                prof.get("office"),
                prof.get("hours"),
                None,  # department not in raw extraction
                source_file_id,
                now,
            ),
        )

    # TAs
    for ta in data.get("tas", []):
        if ta.get("name"):
            await db.execute(
                """
                INSERT INTO ta_info
                    (id, class_id, name, email, office_hours, source_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    class_id,
                    ta.get("name"),
                    ta.get("email"),
                    ta.get("hours"),
                    source_file_id,
                    now,
                ),
            )

    # Grading weights
    for item in data.get("grading", []):
        if item.get("component"):
            await db.execute(
                """
                INSERT INTO grading_weights
                    (id, class_id, component, weight_pct, source_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    class_id,
                    item.get("component"),
                    item.get("weight_pct"),
                    source_file_id,
                    now,
                ),
            )

    # Required materials
    for mat in data.get("materials", []):
        if mat.get("title"):
            await db.execute(
                """
                INSERT INTO required_materials
                    (id, class_id, material_type, title, author, edition,
                     isbn, notes, added_to_class, source_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    class_id,
                    mat.get("type"),
                    mat.get("title"),
                    mat.get("author"),
                    mat.get("edition"),
                    mat.get("isbn"),
                    None,
                    source_file_id,
                    now,
                ),
            )

    # Course schedule + lecture placeholders
    for idx, entry in enumerate(data.get("schedule", []), start=1):
        lecture_id = str(uuid.uuid4())
        topic = entry.get("topic", "")
        week_or_date = entry.get("week_or_date", "")

        # Create a lecture placeholder
        await db.execute(
            """
            INSERT INTO lectures
                (id, class_id, number, date, title, transcript_path,
                 reference_file_path, created_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (lecture_id, class_id, idx, week_or_date, topic, now),
        )

        # Create corresponding course_schedule entry
        await db.execute(
            """
            INSERT INTO course_schedule
                (id, class_id, week_number, scheduled_date, topic, chapters,
                 linked_lecture_id, source_file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                class_id,
                idx,
                week_or_date,
                topic,
                entry.get("chapters"),
                lecture_id,
                source_file_id,
                now,
            ),
        )

    # Calendar events
    for event in data.get("events", []):
        if event.get("title"):
            await db.execute(
                """
                INSERT INTO calendar_events
                    (id, class_id, title, event_date, event_type, location,
                     notes, source_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    class_id,
                    event.get("title"),
                    event.get("date"),
                    event.get("type"),
                    event.get("location"),
                    source_file_id,
                    now,
                ),
            )

    await db.commit()


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def compute_syllabus_diff(old_data: dict[str, Any], new_data: dict[str, Any]) -> dict:
    """Compare two syllabus extraction dicts and return a change summary.

    Returns ``{changed: list, added: list, removed: list}`` for the
    ``events`` list, keyed by event title.
    """
    def events_by_title(data: dict) -> dict[str, dict]:
        return {e["title"]: e for e in data.get("events", []) if e.get("title")}

    old_events = events_by_title(old_data)
    new_events = events_by_title(new_data)

    old_titles = set(old_events)
    new_titles = set(new_events)

    added = [new_events[t] for t in new_titles - old_titles]
    removed = [old_events[t] for t in old_titles - new_titles]
    changed = [
        new_events[t]
        for t in old_titles & new_titles
        if old_events[t] != new_events[t]
    ]

    return {"changed": changed, "added": added, "removed": removed}
