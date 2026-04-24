"""
BRAIN.md file generator and updater for YakAI.

The BRAIN file is the per-class AI knowledge base. It is a Markdown document
with YAML front-matter that the sidecar injects as context into every API call.
"""

from __future__ import annotations

import os
import re
from typing import Any


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

def _lecture_entries(references: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for ref in references:
        title = ref.get("title") or "Untitled"
        date = ref.get("date") or ""
        path = ref.get("reference_file_path") or ""
        date_str = f" ({date})" if date else ""
        link = f"[references/{os.path.basename(path)}]" if path else ""
        lines.append(f"- [{title}{date_str}]({link})")
    return "\n".join(lines) if lines else "- (none yet)"


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_brain_file(
    class_info: dict[str, Any],
    references: list[dict[str, Any]] | None = None,
) -> str:
    """Build the full BRAIN.md content string from class metadata."""
    if references is None:
        references = []

    slug = class_info.get("slug", "unknown-class")
    course_code = class_info.get("course_code", "")
    course_name = class_info.get("course_name", "")
    professor = class_info.get("professor") or "TBD"
    semester = class_info.get("semester") or ""
    major = class_info.get("major") or ""
    description = (
        f"Complete knowledge base for {professor}'s {course_name} course"
        + (f", {semester}" if semester else "")
        + "."
    )

    lecture_section = _lecture_entries(references)

    return f"""---
name: {slug}
description: "{description}"
course-code: {course_code}
course-name: {course_name}
professor: {professor}
semester: {semester}
major: {major}
exam-focus: []
inherited-from: []
---

# {course_code} — {course_name}

## When to Use This Brain
- User asks for a quiz on any topic
- User sends a message in the class chat
- User needs homework help
- User wants a summary or key points
- User asks to generate a practice exam
- User searches for a concept

## ⚠️ Hard Constraints
- NEVER use a solving method not found in the references below
- NEVER guess or hallucinate formula values
- NEVER give a partial answer — show all steps or say you can't
- If knowledge is missing: "I don't have enough training on [topic] yet. Try adding your notes."
- Math must be exact. Always show full working.

## Course Topics (Master Index)

| Topic | Covered In | Exam Weight |
|---|---|---|

## Key Formulas (Class-Approved Only)

## Exam Flags

## Lecture Index
{lecture_section}

## Documents & Slides

## Homework

## Past Exams (Reference Only — Not Course Canon)

## YouTube References (Supplementary — Not Course Canon)

## Inherited Knowledge
- (none)
"""


# ---------------------------------------------------------------------------
# Writer / updater
# ---------------------------------------------------------------------------

async def write_brain_file(brain_path: str, content: str) -> None:
    """Write *content* to *brain_path*, creating parent directories as needed."""
    os.makedirs(os.path.dirname(brain_path), exist_ok=True)
    with open(brain_path, "w", encoding="utf-8") as fh:
        fh.write(content)


async def update_brain_file(brain_path: str, section: str, new_entry: str) -> None:
    """Append *new_entry* under the first occurrence of *section* heading.

    If the section is not found the entry is appended at the end.
    """
    with open(brain_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Find the section heading and insert after the last non-empty line in it
    heading = f"## {section}"
    pattern = re.compile(
        rf"(## {re.escape(section)}.*?)(\n## |\Z)", re.DOTALL
    )
    match = pattern.search(content)
    if match:
        insert_pos = match.end(1)
        content = content[:insert_pos] + "\n" + new_entry + content[insert_pos:]
    else:
        content = content.rstrip("\n") + f"\n\n## {section}\n{new_entry}\n"

    with open(brain_path, "w", encoding="utf-8") as fh:
        fh.write(content)
