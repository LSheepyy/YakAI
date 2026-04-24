"""
Quiz generator and answer grader — uses GPT-4o for generation, GPT-4o-mini
for grading (cheaper per question).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

QUIZ_SYSTEM_PROMPT = """\
You are an expert professor creating quiz questions.
You MUST base every question EXCLUSIVELY on the course material provided in
the context below.  Do NOT invent questions about topics not found in the
context.

Rules:
- Generate ONLY the number of questions requested.
- For "mcq" questions include exactly 4 answer choices labelled A, B, C, D
  in the correct_answer field — write the full letter + answer, e.g. "A. Newton's first law".
- For "short-answer" questions, correct_answer should be a concise model answer (1-3 sentences).
- Each question must have three progressive hints:
    hint_level_1: vague nudge (no answer)
    hint_level_2: stronger hint (still no answer)
    hint_level_3: near-answer
- topic_tag: a short topic label matching the course material, e.g. "Kinematics" or "Cell Division".
- If grading_weights are provided, bias the question distribution proportionally.
- Return ONLY valid JSON — a JSON array of question objects. No markdown fences, no explanations.

JSON schema for each question:
{
  "question_text": "...",
  "correct_answer": "...",
  "question_type": "mcq" | "short-answer",
  "hint_level_1": "...",
  "hint_level_2": "...",
  "hint_level_3": "...",
  "topic_tag": "..."
}
"""

_GRADER_SYSTEM_PROMPT = """\
You are a strict but fair grader.  Given a question, the correct answer, and
a student's answer, decide whether the student's answer is correct.

Rules:
- Minor spelling/formatting differences are OK.
- For MCQ: the student must identify the correct letter OR the correct full answer text.
- For short-answer: the core concept must be present; minor omissions are acceptable.
- Return ONLY valid JSON: {"is_correct": true/false, "explanation": "brief reason"}
"""


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

async def generate_quiz_questions(
    openai_client: Any,
    context_chunks: list[dict[str, Any]],
    num_questions: int = 10,
    question_types: list[str] | None = None,
    grading_weights: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate quiz questions grounded in *context_chunks*.

    Returns a list of question dicts matching the JSON schema above.
    """
    if question_types is None:
        question_types = ["mcq", "short-answer"]
    if grading_weights is None:
        grading_weights = []

    if not context_chunks:
        logger.warning("generate_quiz_questions: no context chunks provided")
        return []

    # Build context block
    context_parts: list[str] = []
    for chunk in context_chunks:
        source = chunk.get("source_name", "Unknown")
        text = chunk.get("text", "")
        context_parts.append(f"[{source}]\n{text}")
    context_text = "\n\n---\n\n".join(context_parts)

    # Grading weights guidance
    weights_note = ""
    if grading_weights:
        weight_lines = [
            f"  - {w.get('component', '?')}: {w.get('weight_pct', 0)}%"
            for w in grading_weights
        ]
        weights_note = (
            "\n\nGrading weights (bias question distribution accordingly):\n"
            + "\n".join(weight_lines)
        )

    user_prompt = (
        f"Generate {num_questions} quiz questions.\n"
        f"Question types to include: {', '.join(question_types)}.\n"
        f"{weights_note}\n\n"
        f"Course material:\n{context_text}"
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    raw: str = response.choices[0].message.content or "[]"

    questions = _parse_questions(raw)
    logger.info("generate_quiz_questions: generated %d questions", len(questions))
    return questions


def _parse_questions(raw: str) -> list[dict[str, Any]]:
    """Parse GPT JSON output into a list of question dicts."""
    try:
        data = json.loads(raw)
        # GPT may wrap the array in a key like "questions"
        if isinstance(data, dict):
            for key in ("questions", "quiz", "items", "data"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
            else:
                # Try the first list value
                for val in data.values():
                    if isinstance(val, list):
                        data = val
                        break
                else:
                    data = []
        if not isinstance(data, list):
            return []
        return [q for q in data if isinstance(q, dict)]
    except (json.JSONDecodeError, ValueError):
        logger.warning("_parse_questions: could not parse JSON, attempting regex extraction")
        return _extract_questions_regex(raw)


def _extract_questions_regex(raw: str) -> list[dict[str, Any]]:
    """Fallback: extract JSON objects from raw text via regex."""
    pattern = re.compile(r"\{[^{}]*\"question_text\"[^{}]*\}", re.DOTALL)
    questions: list[dict[str, Any]] = []
    for match in pattern.finditer(raw):
        try:
            q = json.loads(match.group())
            questions.append(q)
        except json.JSONDecodeError:
            continue
    return questions


# ---------------------------------------------------------------------------
# Answer grading
# ---------------------------------------------------------------------------

async def grade_answer(
    openai_client: Any,
    question_text: str,
    correct_answer: str,
    user_answer: str,
) -> tuple[bool, str]:
    """Grade *user_answer* against *correct_answer* for *question_text*.

    Returns (is_correct, explanation).
    Uses GPT-4o-mini to keep grading costs low.
    """
    user_prompt = (
        f"Question: {question_text}\n"
        f"Correct answer: {correct_answer}\n"
        f"Student's answer: {user_answer}"
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _GRADER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    raw: str = response.choices[0].message.content or "{}"
    try:
        result = json.loads(raw)
        is_correct = bool(result.get("is_correct", False))
        explanation = str(result.get("explanation", ""))
    except (json.JSONDecodeError, ValueError):
        logger.warning("grade_answer: could not parse grader JSON: %s", raw[:200])
        is_correct = False
        explanation = "Could not evaluate your answer. Please try again."

    return is_correct, explanation
