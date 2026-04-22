"""
update_skills_index.py

Scans ~/.claude/agents/, ~/.claude/commands/, and ~/.claude/skills/,
reads name + description from each skill's frontmatter, categorises
everything, and writes ~/.claude/SKILLS_INDEX.md.

Run directly:  python ~/.claude/scripts/update_skills_index.py
Or via:        /update-skills-index  (Claude slash command)
"""

import os
import re
import sys
from pathlib import Path
from datetime import date

CLAUDE_DIR = Path.home() / ".claude"
AGENTS_DIR  = CLAUDE_DIR / "agents"
COMMANDS_DIR = CLAUDE_DIR / "commands"
SKILLS_DIR  = CLAUDE_DIR / "skills"
OUTPUT_FILE = CLAUDE_DIR / "SKILLS_INDEX.md"

# ── Category rules ────────────────────────────────────────────────────────────
# Evaluated in order — first match wins.
# Each rule: (category_name, [keywords_in_name_or_description])
CATEGORIES = [
    ("Memory & Sessions",       ["memory", "session", "mem-search", "resume-session", "save-session", "instinct", "checkpoint"]),
    ("Planning & Architecture", ["plan", "architect", "feature-dev", "prp-plan", "prp-prd", "prp-implement", "multi-plan", "multi-workflow", "orchestrat"]),
    ("Code Review & Quality",   ["review", "reviewer", "quality", "simplif", "cleaner", "clean", "refactor", "prune", "comment-analyz", "silent-failure", "type-design"]),
    ("Testing",                 ["tdd", "test", "e2e", "coverage", "eval", "regression", "verification"]),
    ("Build & Debugging",       ["build", "resolver", "error", "fix", "debug", "compile", "gradle", "cmake"]),
    ("Security",                ["security", "auth", "vulnerability", "owasp", "sanitiz", "opensource-sanitiz"]),
    ("Documentation",           ["doc", "readme", "codemap", "update-doc", "changelog", "code-tour"]),
    ("Git & PRs",               ["git", "prp-commit", "prp-pr", "review-pr", "commit", "branch", "pr-test"]),
    ("Frontend & Design",       ["frontend", "ui-", "ux", "design", "css", "styling", "banner", "brand", "theme", "canvas", "slides", "artifact"]),
    ("Database",                ["database", "sql", "query", "schema", "migration"]),
    ("Performance",             ["performance", "optim", "speed", "bundle", "latency"]),
    ("Accessibility",           ["a11y", "accessibility", "wcag"]),
    ("SEO & Marketing",         ["seo", "marketing", "content", "copy", "email", "social", "ad-", "brand", "cro", "churn", "lead", "competitor", "launch", "pricing", "paid-ads", "programmatic", "twitter", "community", "aso-", "domain-name"]),
    ("AI & Claude API",         ["pytorch", "claude-api", "anthropic", "llm", "prompt-optim", "ai-seo", "ai-regression", "langsmith", "eval-harness"]),
    ("DevOps & Infrastructure", ["deploy", "docker", "ci-", "pm2", "devfleet", "multi-backend", "multi-frontend", "multi-execute"]),
    ("Open Source",             ["opensource"]),
    ("Language: Python",        ["python"]),
    ("Language: TypeScript/JS", ["typescript", "javascript"]),
    ("Language: Go",            ["golang", "go-"]),
    ("Language: Rust",          ["rust"]),
    ("Language: Kotlin/Android",["kotlin", "android"]),
    ("Language: Flutter/Dart",  ["flutter", "dart"]),
    ("Language: Java/Spring",   ["java", "springboot", "spring"]),
    ("Language: C++",           ["cpp", "c++"]),
    ("Language: C#/.NET",       ["csharp", "dotnet"]),
    ("Language: Swift",         ["swift"]),
    ("Language: PHP/Laravel",   ["php", "laravel"]),
    ("Language: Perl",          ["perl"]),
    ("Mobile",                  ["android", "flutter", "compose-multiplatform", "kotlin-coroutines", "kotlin-ktor"]),
    ("Project Management",      ["jira", "project", "revops", "sales", "customer", "meeting", "strategic", "product-marketing"]),
    ("MCP & Plugins",           ["mcp-builder", "mcp-server", "connect", "configure-ecc", "hookify", "update-config"]),
    ("Developer Utilities",     ["file-organiz", "invoice", "raffle", "defuddle", "image-enhancer", "json-canvas", "obsidian", "instruct", "learn", "skill-", "rules-distill", "agent-sort", "loop", "context-budget", "promote", "sessions", "projects", "resume-session", "aside", "council", "prune", "harness", "model-route"]),
]

FALLBACK_CATEGORY = "Utilities"


def read_frontmatter(path: Path) -> dict:
    """Extract name and description from YAML frontmatter."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {"name": path.stem, "description": ""}

    fm = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    if "name" not in fm:
        fm["name"] = path.stem
    return fm


def collect_skills() -> list[dict]:
    skills = []

    # agents — single .md files
    if AGENTS_DIR.exists():
        for f in sorted(AGENTS_DIR.glob("*.md")):
            fm = read_frontmatter(f)
            skills.append({
                "type": "agent",
                "name": fm.get("name", f.stem),
                "description": fm.get("description", ""),
                "invoke": f"use {fm.get('name', f.stem)} agent",
            })

    # commands — single .md files (slash commands)
    if COMMANDS_DIR.exists():
        for f in sorted(COMMANDS_DIR.glob("*.md")):
            fm = read_frontmatter(f)
            skills.append({
                "type": "command",
                "name": f.stem,
                "description": fm.get("description", ""),
                "invoke": f"/{f.stem}",
            })

    # skills — directories with SKILL.md inside
    if SKILLS_DIR.exists():
        for d in sorted(SKILLS_DIR.iterdir()):
            skill_file = d / "SKILL.md"
            if not skill_file.exists():
                skill_file = d / "skill.md"
            if not skill_file.exists():
                continue
            fm = read_frontmatter(skill_file)
            skills.append({
                "type": "skill",
                "name": fm.get("name", d.name),
                "description": fm.get("description", ""),
                "invoke": f"/{d.name}",
            })

    return skills


def categorise(skill: dict) -> str:
    haystack = (skill["name"] + " " + skill["description"]).lower()
    for category, keywords in CATEGORIES:
        if any(kw in haystack for kw in keywords):
            return category
    return FALLBACK_CATEGORY


def build_index(skills: list[dict]) -> str:
    # Group by category preserving insertion order
    groups: dict[str, list] = {}
    for skill in skills:
        cat = categorise(skill)
        groups.setdefault(cat, []).append(skill)

    # Sort categories alphabetically, but keep high-value ones first
    priority = [
        "Planning & Architecture", "Code Review & Quality", "Testing",
        "Build & Debugging", "Security", "Memory & Sessions",
    ]
    ordered = priority + sorted(k for k in groups if k not in priority)

    lines = [
        "# Skills Index",
        f"_Auto-generated {date.today()}. Run `/update-skills-index` to refresh after installing new skills._",
        "",
        "## How Claude uses this",
        "When you send a prompt, Claude reads the relevant category here to identify",
        "the best skill for the job — without loading every skill file upfront.",
        "",
        f"**Total: {len(skills)} skills across {len(groups)} categories.**",
        "",
        "---",
        "",
    ]

    type_symbol = {"agent": "🤖", "command": "⚡", "skill": "📖"}

    for cat in ordered:
        if cat not in groups:
            continue
        items = groups[cat]
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| Invoke | Type | What it does |")
        lines.append("|--------|------|-------------|")
        for s in items:
            sym = type_symbol.get(s["type"], "•")
            invoke = f"`{s['invoke']}`"
            desc = s["description"][:90].replace("|", "\\|") if s["description"] else "—"
            lines.append(f"| {invoke} | {sym} {s['type']} | {desc} |")
        lines.append("")

    return "\n".join(lines)


def main():
    print("Scanning skill directories…")
    skills = collect_skills()
    print(f"  Found {len(skills)} skills ({sum(1 for s in skills if s['type']=='agent')} agents, "
          f"{sum(1 for s in skills if s['type']=='command')} commands, "
          f"{sum(1 for s in skills if s['type']=='skill')} skills)")

    index = build_index(skills)
    OUTPUT_FILE.write_text(index, encoding="utf-8")
    print(f"  Written -> {OUTPUT_FILE}")

    # Print category summary
    from collections import Counter
    cats = Counter(categorise(s) for s in skills)
    print("\nCategory breakdown:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {cat}")


if __name__ == "__main__":
    main()
