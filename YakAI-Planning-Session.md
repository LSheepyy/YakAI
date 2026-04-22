# YakAI — Planning Session Notes

> Date: 2026-04-22
> Participants: Avery + Claude
> Full plan: [[YakAI-Plan]]

This note captures the key decisions and reasoning from the initial planning session for YakAI. Use [[YakAI-Plan]] as the living source of truth — this file is a record of *why* decisions were made.

---

## What YakAI Is

A cross-platform desktop app (Tauri + React + Python) that turns a student's class materials into a per-class AI expert. The AI only knows what was actually taught — it never uses external knowledge, never hallucinates, and explicitly says when it doesn't have enough information.

Target user: any university student, any major. The AI adapts to whatever subject it's given.

---

## Key Decisions Made This Session

### Tech Stack
- **Tauri over Electron** — lighter, faster, better for an offline-first app on student laptops
- **Python sidecar** — Python has the best libraries for AI, audio, and file processing (Whisper, ChromaDB, PyMuPDF, FFmpeg)
- **GPT-4o for everything visual** — GPT-4o has vision built in natively. No separate Vision API service. Pass images directly into the same API call.
- **GPT-4o-mini for lightweight tasks** — summaries, keyword extraction, calendar parsing. ~20x cheaper than GPT-4o, more than capable enough.
- **Local Whisper (small model default)** — fully offline transcription. User can opt into medium model in Settings for better accuracy on technical speech.
- **ChromaDB locally** — all vector embeddings live on the user's machine. The "training" is actually RAG, not fine-tuning.

### The BRAIN File System
- Every class gets a folder with a master `.md` file named `[COURSE-CODE]-[slug].md`
- Structured exactly like the [legacy-circuit-mockups SKILL.md](https://github.com/github/awesome-copilot/tree/main/skills/legacy-circuit-mockups): frontmatter metadata, hard constraints, topic index, formulas, lecture index, exam flags, references
- Each lecture/document gets its own reference `.md` file inside `references/`
- Raw files (PDFs, videos) kept in `raw/` — user can delete these to save space; the processed reference data is preserved

### App Data Directory
- Tauri `app_data_dir()` resolves the correct platform path at runtime
- Windows: `%APPDATA%\YakAI\`, Mac: `~/Library/Application Support/YakAI/`, Linux: `~/.local/share/YakAI/`
- Python sidecar receives this path from Tauri as an environment variable — no hardcoded paths anywhere

### Whisper Model
- Default: `small` (244 MB) — fast, good accuracy
- Optional: `medium` (769 MB) — downloaded on demand via Settings, better for heavy technical vocabulary

### Features Added During Session (not in original notes)
- **Free-form chat per class** — the most natural use case. Each class has its own chat window scoped to that class's BRAIN. Ask anything, get answers grounded only in what was taught.
- **Semantic search** — ChromaDB-powered search across all class content. Find concepts, transcripts, formulas across lectures.
- **Data backup / export / import / class sharing** — export a class as `.yakclass` (zipped folder + SQLite rows + ChromaDB embeddings). Import on another machine or share with a classmate.
- **Python sidecar lifecycle** — explicit startup loading state, request queue while sidecar starts, automatic crash recovery.
- **API cost transparency** — every API call logged, running monthly estimate in Settings, pre-processing cost warning for large files.
- **Better onboarding for API key** — step-by-step with screenshots (generated via artifacts-builder skill), cost warnings, key validation.

### What We Decided NOT to Do (Yet)
- Code signing / app store distribution — not a priority while still building core features
- Subscription / auth / cloud sync — parked for far future
- iPad/mobile — Tauri doesn't target iOS, out of scope for v1

---

## Collaboration

- **Avery** → everything in `apps/desktop/src/` (React frontend, all screens, Tauri shell config)
- **Tommy Huynh** ([@Tommy-Huynh-GIT](https://github.com/Tommy-Huynh-GIT)) → everything in `services/ai-core/` (Python sidecar, all AI, file processing)
- **Both** → SQLite schema, shared types / API contract, integration tests, CI/CD setup

---

## Build Order (5 Phases)

1. **Foundation** — app shell, class management, PDF ingestion, BRAIN generation, CI/CD
2. **Core AI Loop** — RAG, chat mode, search, quiz engine, homework help, cost tracking
3. **Media Ingestion** — audio recording, Whisper, video processing, slides, images
4. **Smart Features** — calendar, past exam mode, YouTube, backup/export/import
5. **Polish** — dark mode, keyboard shortcuts, onboarding refinement, cross-platform testing

---

## Still Open

- YakAI logo / branding
- Diagram generation format (Mermaid/D2 structured vs GPT-4o ad-hoc)
- Timestamped note-taking during recording (Phase 4 candidate)
- Markdown export for Obsidian/Notion users (low effort, Phase 4)
