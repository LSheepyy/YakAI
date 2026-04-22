# YakAI — Full Project Plan

> Last updated: 2026-04-22
> A cross-platform AI-powered desktop study assistant. Students add their class
> materials (lectures, textbooks, slides, recordings) and YakAI becomes an expert
> on each individual class — generating quizzes, summaries, mock exams, homework
> help, free-form chat, and a full study calendar, using only what was actually taught.

---

## Table of Contents

1. [Vision & Core Philosophy](#1-vision--core-philosophy)
2. [Tech Stack](#2-tech-stack)
3. [Repository & Team Split](#3-repository--team-split)
4. [App Architecture Overview](#4-app-architecture-overview)
5. [The BRAIN File System (per class)](#5-the-brain-file-system-per-class)
6. [File Ingestion — Smart Type Detection](#6-file-ingestion--smart-type-detection)
7. [Feature Modules](#7-feature-modules)
8. [Data Model (SQLite)](#8-data-model-sqlite)
9. [UI Layout — Screen by Screen](#9-ui-layout--screen-by-screen)
10. [App Data Directory](#10-app-data-directory)
11. [Python Sidecar Lifecycle](#11-python-sidecar-lifecycle)
12. [API Cost Transparency](#12-api-cost-transparency)
13. [Testing Strategy](#13-testing-strategy)
14. [Build Phases](#14-build-phases)
15. [Collaboration Split](#15-collaboration-split)
16. [Future Business Notes](#16-future-business-notes)
17. [Open Questions / Later Decisions](#17-open-questions--later-decisions)

---

## 1. Vision & Core Philosophy

YakAI is a desktop application where students organize their university courses and feed in all their class material. The app turns that material into a per-class AI expert — one that only knows what was actually taught, never hallucinates, never uses methods from outside the course, and gets smarter the more you give it.

### Hard Rules the AI Always Follows
- **Never use a method not found in the class materials.** If the professor taught one way to solve a circuit, that is the only way YakAI solves it.
- **Never hallucinate formulas, values, or steps.** If the answer isn't derivable from what was given, say so explicitly.
- **Missing knowledge response:** `"I don't have enough training on this topic yet. Try adding your textbook chapter or lecture notes on [topic]."`
- **Math is always exact.** Every calculation shows full step-by-step working.
- **Diagrams are rendered as images.** When a diagram is part of an answer, it is shown visually — not described in text.

### What Makes YakAI Different
- The AI per class is scoped — it knows your professor's specific methods, not just general knowledge.
- Everything is organized like a real university: Semesters → Courses → Lectures.
- One import box. Drop anything in. The app figures out what it is.
- Recording works in the background during class. You walk out with a transcript, summary, and key points.
- Performance tracking across every quiz — YakAI knows where you're weak and drills those areas harder.
- Free-form chat per class — ask anything about the material, get answers grounded only in what was taught.

---

## 2. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| App shell | **Tauri** (Rust + WebView) | Lighter than Electron, cross-platform (Windows/Mac/Linux), offline-first, smaller install size |
| Frontend | **React + TypeScript** | Component-driven, strong ecosystem, good for dashboards and interactive UIs |
| Styling | **Tailwind CSS** | Fast iteration, consistent design system, no CSS bloat |
| Backend / AI logic | **Python sidecar** (FastAPI) | Best ecosystem for AI, audio, file processing — Whisper, PyMuPDF, ChromaDB all live here |
| AI — primary | **GPT-4o** (user's OpenAI key) | Handles text reasoning, quiz generation, homework help, chat AND all visual analysis (images, diagrams, video frames, slides) natively in the same API call — no separate vision service needed |
| AI — lightweight tasks | **GPT-4o-mini** (same key) | Used for low-stakes tasks: summaries, keyword extraction, duplicate text fingerprinting. ~20x cheaper than GPT-4o |
| Audio transcription | **Whisper (local)** — `small` model by default, `medium` opt-in in Settings | Fully offline, no per-minute API cost. `small` (244 MB) is the default — fast and accurate enough for lecture audio. User can switch to `medium` (769 MB) in Settings for better accuracy on complex technical speech |
| Local vector database | **ChromaDB** (local) | Semantic search over all class material — powers RAG (Retrieval Augmented Generation) |
| Structured storage | **SQLite** | Classes, quizzes, performance tracking, calendar events, file registry |
| PDF parsing | **PyMuPDF** | Fast, accurate text + image extraction from PDFs |
| Slide parsing | **python-pptx** | Extract per-slide text and embedded images from PowerPoint files |
| Video/audio processing | **FFmpeg** | Noise reduction, audio amplification before Whisper transcription, frame extraction from videos |
| YouTube ingestion | **yt-dlp** | Download YouTube audio/video for processing — stored separately from course canon |
| Diagram rendering | **React canvas / SVG** | Render AI-described diagrams as actual visual output in the frontend |
| Cross-platform builds | **GitHub Actions + Tauri build matrix** | Automatically builds Windows (.msi) and Mac (.dmg) binaries on every release |

### Why GPT-4o Handles All Visual Analysis
GPT-4o has vision built directly into the model — it is not a separate API service. When YakAI needs to analyze an image (a slide, a diagram, a video frame, a photo of a whiteboard), it passes that image as part of the standard API message. No extra API key, no extra service, no extra cost category. The same call that generates a quiz can also describe a circuit diagram. This simplifies the entire architecture.

### GPT-4o vs GPT-4o-mini Routing

| Task | Model | Why |
|---|---|---|
| Quiz generation | GPT-4o | Needs accuracy and reasoning |
| Homework help | GPT-4o | Needs accuracy and full working |
| Free-form chat | GPT-4o | Needs understanding and nuance |
| Image / diagram analysis | GPT-4o | Vision requires the full model |
| Lecture summary | GPT-4o-mini | Low-stakes, saves cost |
| Keyword / topic extraction | GPT-4o-mini | Simple classification task |
| Duplicate text fingerprinting | GPT-4o-mini | Very simple comparison |
| Calendar event extraction from syllabus | GPT-4o-mini | Structured extraction, not complex |

### Why RAG Instead of Fine-Tuning
"Training the AI on a class" in YakAI means **Retrieval Augmented Generation (RAG)** — not actual model fine-tuning.

How it works:
1. Every document, lecture, and video you add gets chunked into small pieces and embedded into ChromaDB as vectors.
2. When you ask a question, generate a quiz, or chat, ChromaDB finds the most relevant chunks from your class materials.
3. Those chunks are injected into the API prompt alongside a hard constraint: "only use what's provided."
4. The AI answers using only the retrieved material — no general internet knowledge leaking in.

This means the AI is effectively "re-trained" on your class every time you add a new file. No waiting, no extra cost beyond the API call.

---

## 3. Repository & Team Split

### Monorepo Structure
```
yakai/
├── apps/
│   └── desktop/              ← Tauri app
│       ├── src-tauri/        ← Rust shell (file system, app lifecycle, OS tray)
│       └── src/              ← React frontend
│           ├── components/
│           ├── screens/
│           ├── hooks/
│           └── stores/
├── services/
│   └── ai-core/              ← Python FastAPI sidecar
│       ├── ingestor/         ← file type detection + processing
│       ├── brain/            ← BRAIN.md builder + updater
│       ├── quiz/             ← quiz generation engine
│       ├── chat/             ← free-form chat handler
│       ├── search/           ← semantic search
│       ├── rag/              ← ChromaDB + retrieval
│       ├── whisper/          ← audio transcription
│       ├── calendar/         ← syllabus parser
│       └── backup/           ← export / import / restore
├── shared/
│   └── types/                ← shared TypeScript + Python type definitions (API contract)
├── .github/
│   └── workflows/
│       └── build.yml         ← GitHub Actions: cross-platform Tauri builds
└── docs/
    └── YakAI-Plan.md         ← this file
```

---

## 4. App Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         YakAI (Tauri)                        │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                  React Frontend                      │   │
│   │                                                      │   │
│   │  Class Hub │ Chat │ Study │ Record │ Calendar        │   │
│   │  Homework Help │ Search │ Settings │ Onboarding      │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │ HTTP (localhost only)              │
│   ┌─────────────────────▼───────────────────────────────┐   │
│   │              Python Sidecar (FastAPI)                │   │
│   │   [starts on app launch, queues requests on startup] │   │
│   │                                                      │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │   │
│   │  │ Ingestor │ │  Brain   │ │    AI Router          │ │   │
│   │  │ Engine   │ │ Builder  │ │ GPT-4o / GPT-4o-mini  │ │   │
│   │  └──────────┘ └──────────┘ └──────────────────────┘ │   │
│   │                                                      │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │   │
│   │  │  Quiz    │ │  Chat    │ │  ChromaDB (RAG)       │ │   │
│   │  │  Engine  │ │  Engine  │ │  local vector store   │ │   │
│   │  └──────────┘ └──────────┘ └──────────────────────┘ │   │
│   │                                                      │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │   │
│   │  │  Search  │ │ Calendar │ │  Whisper (local)      │ │   │
│   │  │  Engine  │ │  Parser  │ │  small / medium       │ │   │
│   │  └──────────┘ └──────────┘ └──────────────────────┘ │   │
│   │                                                      │   │
│   │  ┌──────────┐ ┌──────────┐                          │   │
│   │  │  Backup  │ │Duplicate │                          │   │
│   │  │  Engine  │ │Detector  │                          │   │
│   │  └──────────┘ └──────────┘                          │   │
│   └─────────────────────────────────────────────────────┘   │
│                         │                                    │
│   ┌─────────────────────▼───────────────────────────────┐   │
│   │       SQLite  +  ChromaDB  +  File System            │   │
│   │       (all stored in platform app data directory)    │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. The BRAIN File System (per class)

Every class the user creates gets its own folder. The folder contains a master BRAIN file (named uniquely per class) and a `references/` sub-folder with one file per lecture, document, or processed media.

### Folder Structure
```
{APP_DATA}/
└── data/
    └── Fall-2026/
        └── ENGR2410-circuit-analysis/
            ├── ENGR2410-circuit-analysis.md     ← the class BRAIN file
            ├── meta.json                         ← course metadata
            ├── references/
            │   ├── lecture-01_2026-09-08.md
            │   ├── lecture-02_2026-09-10.md
            │   ├── textbook-chapter-03.md
            │   ├── slides-week-02.md
            │   ├── homework-01.md
            │   ├── homework-01-answers.md
            │   ├── past-exam-2024-midterm.md
            │   └── video-lecture-03-processed.md
            └── raw/
                ├── lecture-03-recording.mp4
                ├── textbook.pdf
                └── slides-week-02.pptx
```

**File naming convention:** `[COURSE-CODE]-[short-slug].md`
- Set when the user creates the class
- Examples: `MATH2210-calculus-3.md`, `PHYS1301-intro-mechanics.md`, `CS3350-os-fundamentals.md`
- Unique and readable outside the app

### The BRAIN File Format

Modeled directly on the [legacy-circuit-mockups SKILL.md](https://github.com/github/awesome-copilot/tree/main/skills/legacy-circuit-mockups) structure.

```markdown
---
name: ENGR2410-circuit-analysis
description: "Complete knowledge base for Dr. Smith's Circuit Analysis course,
  Fall 2026. Use for: quiz generation, homework help, chat, summaries, mock exams.
  CONSTRAINT: Only use methods and formulas covered in the references below."
course-code: ENGR2410
course-name: Circuit Analysis
professor: Dr. Smith
semester: Fall 2026
major: Electrical Engineering
exam-focus: [KVL, KCL, Thevenin, Norton, AC Phasors]
inherited-from: []
---

# ENGR2410 — Circuit Analysis

## When to Use This Brain
- User asks for a quiz on any circuits topic
- User sends a message in the class chat
- User needs homework help on a circuits problem
- User wants a summary or key points from a specific lecture
- User asks to generate a practice exam or mock midterm
- User searches for a concept within this class

## ⚠️ Hard Constraints
- NEVER use a solving method not found in the references below
- NEVER guess or hallucinate formula values
- NEVER give a partial answer — show all steps or say you can't
- If knowledge is missing: "I don't have enough training on [topic] yet.
  Try adding your textbook chapter or lecture notes on this."
- Math must be exact. Always show full working.

## Course Topics (Master Index)

| Topic | Covered In | Exam Weight |
|---|---|---|
| KVL / KCL | Lecture 01, 02 | HIGH |
| Mesh Analysis | Lecture 02, 03 | HIGH |
| Thevenin / Norton | Lecture 04 | HIGH |
| Superposition | Lecture 05 | MEDIUM |
| AC Phasors | Lecture 07, 08 | MEDIUM |
| Op-Amps | Lecture 09 | LOW |

## Key Formulas (Class-Approved Only)
- Ohm's Law: V = IR
- KVL: Sum of voltages around any closed loop = 0
- KCL: Sum of currents entering a node = Sum of currents leaving
- Thevenin: V_th = open-circuit voltage at terminals
- Norton: I_n = short-circuit current at terminals

## Exam Flags
- Sept 15: "KVL mesh analysis WILL be on the midterm"
- Sept 22: "Know how to derive both Thevenin and Norton for any two-terminal network"
- Syllabus: Midterm covers Chapters 1–4, Final is cumulative

## Lecture Index
- [Lecture 01 — Intro + KVL (Sept 8)](references/lecture-01_2026-09-08.md)
- [Lecture 02 — KCL + Mesh Analysis (Sept 10)](references/lecture-02_2026-09-10.md)

## Documents & Slides
- [Textbook Chapter 3](references/textbook-chapter-03.md)
- [Week 2 Slides](references/slides-week-02.md)

## Homework
- [Homework 01](references/homework-01.md)
- [Homework 01 — Answers](references/homework-01-answers.md)

## Past Exams (Reference Only — Not Course Canon)
- [2024 Midterm](references/past-exam-2024-midterm.md)

## YouTube References (Supplementary — Not Course Canon)
- https://youtube.com/... — "Thevenin theorem visual explanation"

## Professor & Contact (from syllabus)
- **Professor:** Dr. Sarah Smith — sarah.smith@university.edu
- **Office:** ENG 214 — Tue/Thu 2:00–4:00pm
- **TAs:** Alex Chen (alex.chen@uni.edu), Priya Patel (p.patel@uni.edu)

## Grading Breakdown (from syllabus)
| Component | Weight |
|---|---|
| Assignments | 20% |
| Quizzes | 10% |
| Midterm | 30% |
| Final Exam | 40% |

## Course Policies (from syllabus)
- **Late submissions:** 10% deducted per day, not accepted after 5 days
- **Attendance:** Not mandatory but exam content is lecture-only
- **Academic integrity:** No collaboration on individual assignments

## Inherited Knowledge
- (none)
```

### Per-Lecture Reference File Format

```markdown
---
lecture: 02
date: 2026-09-10
title: KCL + Mesh Analysis
source: recorded-audio + professor-slides
duration: 52 minutes
---

# Lecture 02 — KCL + Mesh Analysis

## Key Points
- KCL: sum of all currents entering a node equals the sum leaving
- Mesh analysis applies KVL to each independent loop in a planar circuit

## Exam-Flagged Moments
> [32:14] "This setup — two meshes sharing a branch — is exactly the type you'll see on the midterm"

## Formulas Introduced
- I_in = I_out (KCL at a node)
- Mesh current setup: assign clockwise mesh currents, write KVL per loop

## Step-by-Step Method (as taught)
1. Identify all independent loops
2. Assign clockwise mesh current to each (I1, I2, ...)
3. Write KVL equation for each mesh
4. Shared branch current = difference of the two mesh currents
5. Solve the system of equations

## Diagrams
[diagram-lecture02-mesh-example.png]
- Two-mesh circuit with shared resistor R3

## Transcript (with timestamps)
[00:00] "Alright, last class we finished KVL. Today we're doing KCL and mesh..."
[32:14] "This setup — two meshes sharing a branch — is exactly what you'll see on the midterm"
```

---

## 6. File Ingestion — Smart Type Detection

When a user drops any file into a class, the Ingestor runs this decision tree:

```
File received
│
├─ Already seen? (SHA-256 hash + text fingerprint check in SQLite)
│   └─ YES → "This looks like a file you already added ([filename], [date]).
│              Replace it with this version?" → user confirms → overwrite
│
├─ PDF
│   ├─ Dense text, sequential chapters → Textbook / lecture notes
│   │   → PyMuPDF: extract text + embedded images
│   │   → Images passed to GPT-4o for diagram description
│   │   → Chunk + embed into ChromaDB → add to BRAIN references
│   ├─ Contains blanks, numbered questions, point values → Homework
│   │   → Flag as HW → route to Homework Help mode on open
│   └─ Contains dates, "Week X", "Exam", "Assignment Due" → Syllabus
│       → Route to Calendar Parser → GPT-4o-mini extracts all events
│
├─ Video (mp4, mov, mkv, webm)
│   └─ Before processing: show Lecture Assignment Dialog (see below)
│       → User picks a lecture or marks as general
│       → FFmpeg: extract audio → amplify + noise reduce
│       → Whisper (local): full transcript with timestamps
│       → FFmpeg: extract frame every 30s
│       → GPT-4o: analyze each frame — detect board content, diagrams, equations
│       → Save raw file to /raw/, all extracted data to /references/video-XX-processed.md
│       → If assigned to a lecture: reference file is linked to that lecture in SQLite
│           and its content is tagged in ChromaDB with that lecture's ID
│       → If general: tagged as class-wide context, not tied to any specific lecture
│
├─ Audio (mp3, wav, m4a, ogg)
│   └─ FFmpeg: amplify + noise reduce
│       → Whisper (local): transcript with timestamps
│       → GPT-4o-mini: extract key points, GPT-4o flags exam moments
│       → Create lecture reference file
│
├─ Image (jpg, png, webp, heic)
│   └─ GPT-4o: full visual analysis — OCR, diagram recognition, equation reading
│       → If slide/board photo: add to nearest lecture reference
│       → If formula/diagram: add to relevant topic in BRAIN
│
├─ Slides (pptx, key, odp)
│   └─ python-pptx: extract per-slide text + embedded images
│       → GPT-4o: analyze each image slide visually
│       → Create slides reference file (one entry per slide group)
│
├─ YouTube URL (user pastes link)
│   └─ yt-dlp: download audio track
│       → Whisper: transcript
│       → Process like audio above
│       → Stored in BRAIN as "YouTube Reference — supplementary only, not course canon"
│
└─ Unknown type
    └─ "YakAI doesn't recognize this file type. Supported: PDF, MP4, MP3,
       WAV, M4A, JPG, PNG, PPTX, YouTube URLs."
```

### Visual Analysis — How GPT-4o Handles It
GPT-4o does not need a separate "vision service." When analyzing any image — a slide, a video frame, a photo of a whiteboard — YakAI encodes the image as base64 and includes it directly in the GPT-4o API message. The same model that generates quizzes and answers chat messages also reads diagrams, circuit schematics, mathematical notation, and handwritten board notes. One model, one API key, everything.

### Duplicate Detection Detail
- SHA-256 hash of full file content stored in SQLite on every import
- First 15 lines of extracted text stored as a secondary fingerprint
- Match on either triggers the duplicate warning
- Catches the same document re-exported with a different filename

### Video Processing — Special Handling

#### Lecture Assignment Dialog
Shown immediately when a video is dropped in, before any processing begins:

```
You dropped in: lecture-recording.mp4 (1h 42m)

Which lecture is this for?

  ○ Lecture 01 — Intro + KVL (Sept 8)
  ○ Lecture 02 — KCL + Mesh Analysis (Sept 10)
  ○ Lecture 03 — Nodal Analysis (Sept 15)
  ○ Lecture 04 — [no title yet] (Sept 22)
  ○ + Create a new lecture entry for this video
  ○ General class video (not tied to a specific lecture)

[Continue]  [Cancel]
```

- The list shows all existing lecture placeholders for this class (pre-filled from the syllabus if added, or manually created)
- "Create a new lecture entry" lets the user name and date it on the spot before processing
- "General class video" is for supplementary recordings — professor overviews, tutorial videos, review sessions — that cover multiple topics rather than one specific lecture
- This dialog also appears for audio files (same logic applies)

#### Why This Matters for the AI
When a user asks "explain what was covered in Lecture 3," the RAG retriever filters ChromaDB by `lecture_id`. Without lecture tagging, all video content is thrown into a single pool and the AI can't isolate what was covered in a specific session. With it, the AI only pulls content tagged to that lecture — giving precise, focused answers.

**ChromaDB metadata on every video chunk:**
```python
{
  "class_id": "engr2410-circuit-analysis",
  "lecture_id": "lecture-03",          # null if general
  "source_type": "video",
  "scope": "lecture" | "general",
  "filename": "lecture-03-recording.mp4",
  "timestamp_start": 1820,             # seconds into the video
  "timestamp_end": 1890
}
```

When scope is `"general"`, the chunk is still included in full-class queries (homework help, practice exams, free-form chat) — it's just excluded from single-lecture queries like "summarize lecture 2."

#### After Processing
1. Raw file kept in `/raw/` — user can delete later to save space; processed data is preserved
2. A dedicated `video-XX-processed.md` reference file is created: full transcript, timestamp index, frame-by-frame diagram descriptions, key points, exam-flagged moments
3. If assigned to a lecture: the reference file is attached to that lecture entry and the BRAIN lecture index is updated automatically
4. If general: added to the BRAIN under a new "Supplementary Videos" section
5. The lecture entry in the Class Hub schedule updates from `○ [+ Attach recording]` to `✅ [🎥 recorded]`

---

## 7. Feature Modules

### 7.1 Class Management
- Create class: course code, course name, professor, semester, major
- Class inherits-from: optionally link a prior class as background context
- Archive class when done — keeps all data, marks inactive, warns if foundational to declared major
- Delete class: permanently removes BRAIN, ChromaDB embeddings, SQLite records — requires typed confirmation
- Major awareness: app remembers declared major, uses it when generating cross-class context

### 7.2 Free-Form Chat Mode (per class)
Every class has its own dedicated chat window. The chat is scoped to that class's BRAIN — it only knows what has been added to that specific class.

**What the chat can do:**
- Explain concepts in a different way ("explain Thevenin like I've never seen it")
- Compare topics ("what's the difference between mesh and nodal analysis?")
- Give a catch-up on a missed lecture ("summarize what I missed in lecture 3")
- Assess readiness ("am I ready for the midterm based on my quiz performance?")
- Answer ad-hoc questions about the material

**Chat rules (same hard constraints as all other AI features):**
- Only uses material from the class BRAIN
- If asked about something not in the BRAIN: "I don't have enough on this yet — try adding your notes on [topic]"
- Chat history is stored per class in SQLite — user can scroll back through previous sessions
- Chat history is also available as context for new messages (within a session window)

### 7.3 Quiz & Test Engine
**Question types:** MCQ, short answer, step-by-step solve, diagram label, formula fill-in

**Quiz scopes:**
- Single lecture
- Range of lectures (e.g., Lectures 1–5 for midterm prep)
- Full course (final exam mode)
- Weak areas only (weighted by performance data)
- Past exam style (filtered by current semester coverage)

**Hint system:** 3 levels per question, sourced from the reference file the question came from.
Each hint level reduces the score for that question: Level 1 = formula reminder, Level 2 = first step of method, Level 3 = expected value range.

**Performance tracking:** Every attempt stored in SQLite. Topic accuracy calculated per class. Topics below 70% accuracy get 2x weight in next practice session. Dashboard shows topic heat map.

### 7.4 Search
A semantic search bar available from anywhere in the app, scoped to the currently selected class (or optionally across all classes).

**How it works:**
- User types a query (e.g., "phasors" or "how does KVL apply to a loop with 3 resistors")
- ChromaDB performs a vector similarity search across all embedded content for that class
- Results returned ranked by relevance: shows the source (Lecture 03, Textbook Ch. 4, etc.) + the matching excerpt
- Clicking a result opens the relevant reference file

**Search types:**
- Semantic: "explain how mesh analysis works" → finds related content even if those exact words aren't present
- Keyword: "#KVL" prefix for exact phrase search
- Exam-flagged only: filter to show only content the professor flagged as exam material

### 7.5 Recording Module
- Floating overlay widget — stays on top of all windows during class
- Records system microphone via OS audio API
- FFmpeg post-processing: noise reduction + amplification before Whisper
- **Webcam board capture (optional):** frame every 30 seconds, GPT-4o analyzes if board content is present — saves relevant frames with timestamps
- Output: full transcript + timestamp index + summary + key points + extracted diagrams → creates a new lecture reference file → updates BRAIN

### 7.6 Homework Help Mode
- User drops in homework PDF or image
- Ingestor detects question set → routes here automatically
- For each question: ChromaDB retrieves most relevant class material chunks → GPT-4o answers using only those chunks → full step-by-step working + source citation
- "Not enough info" banner if knowledge is insufficient — tells user exactly what topic to add
- If answer key is also added: key's methods are ingested into the BRAIN

### 7.7 Summary & Notes Mode
- Select lecture or range → AI generates structured summary
- Sections: Overview, Key Concepts, Formulas Introduced, Exam Flags, Practice Problems
- Summaries exportable as clean PDF

### 7.8 Syllabus Ingestion

The syllabus is the single richest document a student has at the start of a semester. When a user adds a syllabus to a class, YakAI extracts everything useful from it automatically and distributes that data across the app — populating the calendar, saving professor contact info, pre-filling the lecture schedule, storing grading weights, and flagging required textbooks.

#### What Gets Extracted

**Course identity (updates the class record):**
- Course code, course name, section number, credit count
- Semester and meeting schedule (days, times, room, building)
- Lab or tutorial session times and locations if listed

**Professor & TA info (saved to `professor_info` and `ta_info` tables):**
- Professor name, email, phone (if listed)
- Office location and office hours
- Department / faculty
- TA names, emails, office hours (if listed)
- These are displayed as a contact card in the Class Hub and are easily copyable

**Required materials (saved to `required_materials` table):**
- Textbook titles, authors, editions, ISBNs
- Required software, lab kits, calculators, etc.
- After extraction: "I found your required textbook is [X] — want to add it to this class now?"

**Grading breakdown (saved to `grading_weights` table):**
- Component name and weight (e.g., Assignments 20%, Midterm 30%, Final 40%, Quizzes 10%)
- Used to weight quiz generation — topics on high-weight components get more practice questions
- Displayed as a grade breakdown card in Class Hub

**Course schedule (pre-populates `lectures` table):**
- Week-by-week or date-by-date topic list (e.g., "Week 3: KVL and KCL, Chapter 2")
- Creates placeholder lecture entries with dates and titles
- User can later attach a recording or notes to each placeholder

**Calendar events (saved to `calendar_events` table):**
- Assignment due dates
- Quiz and midterm dates + locations
- Final exam date, time, and room
- Lab submission deadlines
- Reading week / holidays / breaks
- Drop deadline if listed

**Policies (stored in the BRAIN file under a Policies section):**
- Late submission policy
- Attendance policy
- Academic integrity statement (brief, not full legal text)
- These are available to the AI when answering questions like "what happens if I submit late?"

#### Extraction Flow

```
Syllabus PDF/image dropped
    │
    ├─ GPT-4o reads full document
    │   (GPT-4o used here, not mini — syllabus structure varies widely,
    │    needs strong reading comprehension to handle any format)
    │
    ├─ Returns structured JSON:
    │   {
    │     course: { code, name, section, credits, schedule },
    │     professor: { name, email, phone, office, hours },
    │     tas: [ { name, email, hours } ],
    │     materials: [ { type, title, author, edition, isbn } ],
    │     grading: [ { component, weight_pct } ],
    │     schedule: [ { week_or_date, topic, chapters } ],
    │     events: [ { title, date, type, location } ],
    │     policies: { late, attendance, integrity }
    │   }
    │
    ├─ Python sidecar writes each section to SQLite
    ├─ Pre-populates lecture placeholders in `lectures` table
    ├─ Updates class `meta.json` with professor + course info
    ├─ Appends Professor, TA, Grading, Policies sections to BRAIN file
    │
    └─ Frontend shows a confirmation modal:
       "Here's what I found in your syllabus — review and confirm"
```

#### Confirmation Modal (shown to user after extraction)

```
Syllabus processed for ENGR2410

✓ Professor: Dr. Sarah Smith  sarah.smith@university.edu
             Office: ENG 214  |  Hours: Tue/Thu 2–4pm

✓ TAs: Alex Chen (alex.chen@uni.edu), Priya Patel (p.patel@uni.edu)

✓ 14 calendar events added
  (3 assignments, 1 midterm, 1 final, 2 quizzes, 5 lab deadlines, 2 breaks)

✓ Grading: Assignments 20% · Quizzes 10% · Midterm 30% · Final 40%

✓ 13 lecture topics pre-filled in schedule

✓ Required textbook found:
  "Electric Circuits" — Nilsson & Riedel, 11th Ed.
  [+ Add this textbook to the class now]

✓ Policies saved (late submission, attendance, academic integrity)

[Looks good — Save All]   [Edit before saving]
```

The "Edit before saving" option opens an editable form so the user can correct any misread data (e.g., if a date was OCR'd incorrectly) before it's committed to the database.

#### If the Class Was Created Manually (no syllabus yet)
When a class is created, YakAI prompts: *"Do you have your syllabus? Adding it now will pre-fill your schedule, calendar, and professor info."* The user can skip and add it later — the prompt reappears on the Class Hub as a banner until a syllabus has been added.

#### Syllabus Updates
Professors sometimes post an updated syllabus mid-semester (changed exam date, added an assignment). If a second syllabus is dropped in for the same class:
- YakAI detects it's a syllabus (not a duplicate of the first — different content)
- Runs the same extraction
- Shows a diff: "3 calendar events changed, 1 added. Review changes?"
- User approves → existing events are updated, not duplicated

### 7.9 Calendar
- Populated primarily from Syllabus Ingestion (see 7.8)
- Class announcements, professor update emails, and course website posts can also be dropped in → same GPT-4o-mini extraction pipeline
- In-app calendar: color-coded per class, event types: Exam (red), Quiz (orange), Assignment (yellow), Lab (blue), Break/Holiday (gray)
- Clicking any event shows: title, class, type, location, time, and the source file it came from
- OS native notifications for upcoming events (configurable lead time: 1 day, 3 days, 1 week)
- Events can be manually added or edited directly in the calendar

### 7.10 Past Exam Practice Mode
- Past exam PDFs flagged as "reference only — not course canon"
- Practice exam generator: pulls past exam questions, ranks them by similarity to current semester's lecture coverage using ChromaDB, skips topics not yet covered
- Results calibrated to your actual semester — not a raw dump of the old exam

### 7.10 File Cache / Library
- Sub-tab in each class: all files ever added, with type icon, date, size
- Raw files in `/raw/` — user can delete individual ones to save space; processed reference data is preserved
- "View processed data" button opens the reference `.md` file the Ingestor created

### 7.11 Data Backup / Export / Import / Class Sharing
Students invest significant time in their class BRAINs. If a laptop dies, that data should not be lost.

**Export a class:**
- Zips the entire class folder (`BRAIN.md`, all references, raw files) + the SQLite rows for that class + the ChromaDB embeddings
- Produces a single `.yakclass` file (it's just a renamed `.zip`)
- User saves it to cloud storage, external drive, or sends it to a classmate

**Import a class:**
- User drops a `.yakclass` file into YakAI
- App extracts, validates, re-embeds content into local ChromaDB
- If a class with the same code already exists: "This class already exists. Merge, replace, or cancel?"

**Export all data (full backup):**
- Zips the entire `data/` directory + full SQLite database
- Recommended every 30 days — app prompts with a reminder banner if no backup in 30 days

**Class sharing use case:**
- Two students in the same course: one adds all their lecture recordings, the other adds all the textbook chapters
- Each exports their class → the other imports → merges into a combined BRAIN
- Neither needs a server — it's just file exchange

---

## 8. Data Model (SQLite)

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT,
  email TEXT,
  major TEXT,
  openai_api_key_encrypted TEXT,
  whisper_model TEXT DEFAULT 'small',   -- 'small' or 'medium'
  last_backup_at TEXT,
  created_at TEXT
);

CREATE TABLE semesters (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  user_id TEXT REFERENCES users(id)
);

CREATE TABLE classes (
  id TEXT PRIMARY KEY,
  semester_id TEXT REFERENCES semesters(id),
  course_code TEXT NOT NULL,
  course_name TEXT NOT NULL,
  slug TEXT NOT NULL,
  professor TEXT,
  major TEXT,
  brain_file_path TEXT,
  inherited_from_class_id TEXT REFERENCES classes(id),
  is_archived INTEGER DEFAULT 0,
  created_at TEXT
);

CREATE TABLE lectures (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  number INTEGER,
  date TEXT,
  title TEXT,
  transcript_path TEXT,
  reference_file_path TEXT,
  created_at TEXT
);

CREATE TABLE files (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  lecture_id TEXT REFERENCES lectures(id),
  original_filename TEXT,
  stored_path TEXT,
  processed_reference_path TEXT,
  file_type TEXT,   -- pdf, video, audio, image, slides, youtube, homework, syllabus, past-exam
  sha256_hash TEXT,
  text_fingerprint TEXT,
  processed_at TEXT,
  created_at TEXT
);

CREATE TABLE quiz_sessions (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  scope TEXT,         -- lecture, range, full, weak-areas, past-exam
  scope_detail TEXT,
  created_at TEXT
);

CREATE TABLE quiz_questions (
  id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES quiz_sessions(id),
  question_text TEXT,
  correct_answer TEXT,
  question_type TEXT,  -- mcq, short-answer, step-by-step, diagram-label, formula
  hint_level_1 TEXT,
  hint_level_2 TEXT,
  hint_level_3 TEXT,
  source_lecture_id TEXT REFERENCES lectures(id),
  source_file_id TEXT REFERENCES files(id),
  topic_tag TEXT
);

CREATE TABLE quiz_attempts (
  id TEXT PRIMARY KEY,
  question_id TEXT REFERENCES quiz_questions(id),
  user_answer TEXT,
  is_correct INTEGER,
  hints_used INTEGER DEFAULT 0,
  time_taken_seconds INTEGER,
  created_at TEXT
);

CREATE TABLE topic_performance (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  topic_tag TEXT,
  total_attempts INTEGER DEFAULT 0,
  correct_count INTEGER DEFAULT 0,
  accuracy_rate REAL,
  last_updated TEXT
);

CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  role TEXT,          -- 'user' or 'assistant'
  content TEXT,
  created_at TEXT
);

CREATE TABLE calendar_events (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  title TEXT,
  event_date TEXT,
  event_type TEXT,    -- exam, quiz, assignment, lab, lecture, other
  location TEXT,
  notes TEXT,
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);

CREATE TABLE youtube_refs (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  url TEXT,
  title TEXT,
  processed_reference_path TEXT,
  created_at TEXT
);

CREATE TABLE api_usage_log (
  id TEXT PRIMARY KEY,
  model TEXT,         -- 'gpt-4o' or 'gpt-4o-mini'
  tokens_in INTEGER,
  tokens_out INTEGER,
  estimated_cost_usd REAL,
  feature TEXT,       -- 'quiz', 'chat', 'homework', 'ingest', 'summary', etc.
  created_at TEXT
);

-- Syllabus-derived data

CREATE TABLE professor_info (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  name TEXT,
  email TEXT,
  phone TEXT,
  office_location TEXT,
  office_hours TEXT,       -- e.g. "Tue/Thu 2:00–4:00pm, ENG 214"
  department TEXT,
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);

CREATE TABLE ta_info (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  name TEXT,
  email TEXT,
  office_hours TEXT,
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);

CREATE TABLE grading_weights (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  component TEXT NOT NULL,    -- e.g. "Midterm", "Assignments", "Final Exam"
  weight_pct REAL NOT NULL,   -- e.g. 30.0
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);

CREATE TABLE required_materials (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  material_type TEXT,         -- 'textbook', 'software', 'equipment', 'other'
  title TEXT,
  author TEXT,
  edition TEXT,
  isbn TEXT,
  notes TEXT,
  added_to_class INTEGER DEFAULT 0,  -- 1 if user has added this file to the class
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);

CREATE TABLE course_schedule (
  id TEXT PRIMARY KEY,
  class_id TEXT REFERENCES classes(id),
  week_number INTEGER,
  scheduled_date TEXT,
  topic TEXT,
  chapters TEXT,              -- e.g. "Chapter 2–3"
  linked_lecture_id TEXT REFERENCES lectures(id),  -- set when user attaches a recording
  source_file_id TEXT REFERENCES files(id),
  created_at TEXT
);
```

---

## 9. UI Layout — Screen by Screen

### Main Layout
```
┌──────────────────────────────────────────────────────────┐
│  YakAI       [🔍 Search]          [⚙ Settings]           │
├──────────────┬───────────────────────────────────────────┤
│ FALL 2026    │                                           │
│ ▼ ENGR2410  ←│ selected                                  │
│   MATH2210   │                                           │
│   PHYS1301   │                                           │
│              │                                           │
│ SPRING '26   │                                           │
│ ▶ ENGR1101   │                                           │
│  (archived)  │                                           │
│              │                                           │
│ ──────────── │                                           │
│ + New Class  │                                           │
│ 📅 Calendar  │                                           │
│ 💾 Backup    │                                           │
│ ⚙ Settings  │                                           │
└──────────────┴───────────────────────────────────────────┘
```

### Class Hub (main panel when class is selected)
```
ENGR2410 — Circuit Analysis  |  Fall 2026  |  Section 01  |  3 Credits

┌──────────────────────────────────────────────────────┐
│  [📁 Add File / Drop Here]   [🎙 Record Lecture]     │
│  [💬 Chat]  [📝 Quiz Me]  [🧪 Practice Exam]         │
│  [🏠 Homework Help]  [📋 Summary]                    │
└──────────────────────────────────────────────────────┘

┌── Professor ──────────────────────────────────────────┐
│  Dr. Sarah Smith                                      │
│  📧 sarah.smith@university.edu   [Copy]               │
│  📍 ENG 214   🕑 Office hours: Tue/Thu 2:00–4:00pm   │
│                                                       │
│  TAs: Alex Chen (alex.chen@uni.edu)                   │
│       Priya Patel (p.patel@uni.edu)                   │
└───────────────────────────────────────────────────────┘

┌── Grading ──────────────────────────────────────────┐
│  Assignments 20%  Quizzes 10%  Midterm 30%  Final 40% │
└─────────────────────────────────────────────────────┘

Performance Overview
  KVL/KCL ████████░░ 80%  Thevenin ██████░░░░ 62%  AC Phasors ████░░░░░░ 41% ⚠

Schedule (from syllabus)
  ✅ Week 01 (Sept 8)  — Intro + KVL              [🎙 recorded]
  ✅ Week 02 (Sept 10) — KCL + Mesh Analysis      [🎙 recorded]
  ✅ Week 03 (Sept 15) — Nodal Analysis           [🎙 recorded]
  ○  Week 04 (Sept 22) — Thevenin / Norton        [+ Attach recording]
  ○  Week 05 (Sept 29) — Superposition            [+ Attach recording]

Files Added (7)
  📄 textbook.pdf   📊 slides-week-02.pptx   🎥 lecture-03.mp4
  📝 homework-01.pdf   🗒 past-exam-2024.pdf
```

If no syllabus has been added yet, the Professor and Grading cards are replaced with a prompt banner:
```
⚠ No syllabus added yet.
  [+ Add Syllabus] — pre-fills your schedule, calendar, and professor info
```

### Chat Screen (per class)
```
ENGR2410 Chat — Circuit Analysis

┌──────────────────────────────────────────────────────┐
│  [Based on: 3 lectures + textbook ch. 1-4 + 2 HWs]  │
│                                                      │
│  You: explain Thevenin's theorem differently          │
│                                                      │
│  YakAI: Thevenin's theorem says any linear circuit   │
│  with sources can be replaced by a single voltage    │
│  source (V_th) in series with a single resistor      │
│  (R_th). Here's how Dr. Smith's method works:        │
│  [step by step from Lecture 04 reference]            │
│  Source: Lecture 04 — Thevenin/Norton               │
│                                                      │
│  You: ▏                                              │
└──────────────────────────────────────────────────────┘
```

### Study Mode (focused)
- Question displayed center screen, answer input below
- Progress bar: "Question 4 of 20"
- Hint button (reveals incrementally, reduces score)
- Weak area tag: "⚠ This is one of your weak topics"
- After quiz: topic-by-topic breakdown with accuracy bars

### Record Mode (floating overlay)
- Small pill widget, always on top
- `[🔴 REC 00:14:32]  [⏸ Pause]  [⏹ Stop + Process]`
- Webcam toggle (🎥) for board capture

### Onboarding (first launch)
```
Step 1 of 4
Welcome to YakAI — what's your name?
[_______________]

─────────────────────

Step 2 of 4
What's your major?
[_______________]
(YakAI uses this to give better suggestions when
you archive courses or set up class inheritance)

─────────────────────

Step 3 of 4
YakAI uses OpenAI to power your class AI.
You'll need your own OpenAI API key.

How to get one:
  1. Go to platform.openai.com
  2. Sign in or create a free account
  3. Click your profile → "API Keys"
  4. Click "Create new secret key"
  5. Copy the key and paste it below

[sk-••••••••••••••••••••••••••]  [Verify Key ✓]

💡 Typical cost: $5–25/semester depending on
   how much material you add. You control this.
   See openai.com/pricing for details.

─────────────────────

Step 4 of 4
Let's create your first class.
Course code:   [ENGR2410  ]
Course name:   [Circuit Analysis]
Professor:     [Dr. Smith ]
Semester:      [Fall 2026 ▾]
```

---

## 10. App Data Directory

All YakAI data lives in a single root directory resolved by Tauri's `app_data_dir()` API at runtime. Nothing is hardcoded.

| Platform | Path |
|---|---|
| Windows | `C:\Users\{username}\AppData\Roaming\YakAI\` |
| macOS | `/Users/{username}/Library/Application Support/YakAI/` |
| Linux | `/home/{username}/.local/share/YakAI/` |

### Directory Layout
```
{APP_DATA}/
├── data/                    ← all class BRAIN files and raw files
│   └── Fall-2026/
│       └── ENGR2410-circuit-analysis/
│           ├── ENGR2410-circuit-analysis.md
│           ├── references/
│           └── raw/
├── db/
│   └── yakai.db             ← SQLite database
├── chroma/                  ← ChromaDB vector store
├── whisper/
│   └── models/
│       ├── ggml-small.bin   ← default Whisper model (244 MB)
│       └── ggml-medium.bin  ← optional (downloaded on demand, 769 MB)
├── backups/                 ← local backup zips (user can change this path)
└── logs/
    └── sidecar.log          ← Python sidecar logs for debugging
```

**The Python sidecar reads `APP_DATA` from an environment variable set by the Tauri Rust core at launch.** Tommy's sidecar never has a hardcoded path — it always asks Tauri for the correct root. This ensures the same Python code works on Windows, Mac, and Linux.

---

## 11. Python Sidecar Lifecycle

### Startup Sequence
1. Tauri Rust core launches the Python sidecar as a child process on app start
2. Rust sends a health-check HTTP ping to `localhost:{PORT}/health` every 500ms
3. Frontend shows a **"YakAI is starting up..."** splash until the ping returns 200
4. Any requests made while the sidecar is starting are **queued in the frontend** and replayed once the sidecar is ready
5. If startup takes more than 15 seconds: show error with a "Restart AI" button

### During Normal Operation
- Sidecar runs silently in the background
- All communication is localhost HTTP — no network traffic leaves the machine for local operations
- Long-running tasks (video transcription, large PDF ingestion) run as background jobs with progress streamed back to the frontend via Server-Sent Events (SSE)

### Crash Recovery
- If the sidecar process dies unexpectedly, Tauri detects it (child process exit) and:
  1. Shows a non-blocking toast: "AI engine stopped — restarting..."
  2. Automatically relaunches the sidecar
  3. Re-queues any in-flight requests
- If restart fails 3 times in a row: show a persistent error banner with a link to the log file

### Shutdown
- When the user closes YakAI, Tauri sends a graceful shutdown signal to the sidecar
- Sidecar finishes any in-progress writes, flushes SQLite, then exits
- Tauri waits up to 5 seconds before force-killing the process

---

## 12. API Cost Transparency

Students are budget-conscious. YakAI logs every API call and shows running cost estimates.

### Cost Display
- Settings screen shows: **"Estimated API spend this month: $4.20"**
- Breakdown by feature: Ingestion / Quiz / Chat / Homework Help / Summaries
- Powered by the `api_usage_log` SQLite table

### Pre-Processing Cost Warning
Before processing any large file, YakAI estimates cost and warns the user:
```
This video is 2h 14m.
  Whisper transcription: FREE (local)
  Frame analysis (GPT-4o, ~270 frames): ~$1.40 estimated
  Summary (GPT-4o-mini): ~$0.02 estimated
  Total: ~$1.42

[Process]  [Process without frame analysis — FREE]  [Cancel]
```

The "without frame analysis" option still transcribes audio (free via local Whisper) but skips GPT-4o frame scanning — useful for audio-only lectures with no board work.

### Model Cost Reference (approximate, subject to OpenAI pricing changes)
| Model | Input per 1M tokens | Output per 1M tokens |
|---|---|---|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |

---

## 13. Testing Strategy

### Python Sidecar (Tommy owns)
- **Unit tests** for every ingestor module: given a PDF/video/audio/image/slides, verify the correct reference file is produced
- **Unit tests** for the BRAIN builder: adding a new document updates the correct sections
- **Unit tests** for the RAG retriever: given a query and a seeded ChromaDB, verify the right chunks are returned
- **Unit tests** for the duplicate detector: same file twice → triggers duplicate warning
- Framework: `pytest`

### React Frontend (Avery owns)
- **Component tests** for critical UI: Class Hub renders correctly, Quiz question displays properly, Chat message renders
- **Integration smoke tests**: onboarding flow completes, class creation updates the sidebar
- Framework: `Vitest` + `React Testing Library`

### Integration Tests (both)
Critical end-to-end flows verified together:
1. Drop a PDF in → verify BRAIN.md was updated and ChromaDB has new embeddings
2. Record audio → process → verify lecture reference file was created
3. Generate quiz → answer questions → verify SQLite has attempts + topic performance updated
4. Export class → import on a fresh data directory → verify chat and quiz work

### When to Run Tests
- Every PR must pass all unit tests before merge
- Integration tests run manually before any Phase milestone is considered complete
- GitHub Actions runs unit tests on every push to any branch

---

## 14. Build Phases

### Phase 1 — Foundation (Weeks 1–4)
Goal: App opens, you can create a class, drop a PDF in, get a BRAIN file. CI/CD is live.

- [ ] Tauri app shell + React frontend scaffolding
- [ ] GitHub Actions: cross-platform build matrix (Windows + Mac) set up on day 1
- [ ] App data directory resolved via Tauri `app_data_dir()`, passed to Python sidecar
- [ ] Sidebar: semester/class tree (create, rename, archive, delete)
- [ ] SQLite schema (all tables from Section 8)
- [ ] Python sidecar: FastAPI boilerplate, startup/shutdown lifecycle, health check
- [ ] Sidecar startup loading state + crash recovery in frontend
- [ ] PDF ingestion: text + image extraction via PyMuPDF
- [ ] GPT-4o image analysis of embedded PDF images
- [ ] Basic BRAIN file generation from a PDF
- [ ] File registry (hash + text fingerprint, duplicate detection)
- [ ] Onboarding flow (name, major, API key with step-by-step guide, key validation)
- [ ] Syllabus ingestion — GPT-4o extraction of professor info, TA info, grading weights, schedule, calendar events, policies
- [ ] Syllabus confirmation modal (review + edit before saving)
- [ ] Syllabus update detection (second syllabus → show diff, not duplicate warning)
- [ ] Professor contact card + grading breakdown displayed in Class Hub
- [ ] Course schedule pre-population from syllabus (lecture placeholder entries)
- [ ] "No syllabus yet" prompt banner on Class Hub

### Phase 2 — Core AI Loop (Weeks 5–8)
Goal: The AI answers questions, chat works, quizzes work, search works.

- [ ] ChromaDB setup + document embedding pipeline
- [ ] RAG retrieval: "find relevant chunks for this query"
- [ ] **Free-form Chat Mode** — per-class scoped chat window, history stored in SQLite
- [ ] **Semantic Search** — ChromaDB-powered search across class content
- [ ] Homework Help mode (question → RAG → GPT-4o → step-by-step answer + source)
- [ ] Quiz generation (MCQ + short answer + step-by-step)
- [ ] Hint system (3 levels, sourced from reference files)
- [ ] Performance tracking (quiz_attempts + topic_performance tables)
- [ ] Weak area detection + weighted quiz generation
- [ ] BRAIN updater (adding a file updates the master BRAIN.md automatically)
- [ ] GPT-4o vs GPT-4o-mini routing (model selection per task type)
- [ ] API cost logging (`api_usage_log` table) + cost display in Settings

### Phase 3 — Media Ingestion (Weeks 9–12)
Goal: Drop a recording or video in and get a complete lecture reference file.

- [ ] Audio recording in-app (floating overlay widget)
- [ ] FFmpeg: noise reduction + amplification pipeline
- [ ] Whisper (local, `small` model) transcription
- [ ] Whisper model download manager (download `medium` on demand from Settings)
- [ ] Video processing: frame extraction every 30s + GPT-4o visual analysis
- [ ] Video processed `.md` reference file generation
- [ ] Slide (PPTX) ingestion: per-slide text + GPT-4o image analysis
- [ ] Image ingestion: GPT-4o full visual analysis
- [ ] Webcam board capture during recording (optional toggle)
- [ ] Pre-processing cost estimate dialog for large files

### Phase 4 — Smart Features (Weeks 13–16)
Goal: Calendar works, past exams work, YouTube works, backup works, class sharing works.

- [ ] In-app calendar view (all events from syllabus ingestion + manual entries)
- [ ] OS notifications for upcoming events
- [ ] Drop-in class announcements / professor updates → calendar event extraction
- [ ] Required textbook prompt → links to "Add to class" flow
- [ ] Grading weight influence on quiz generation (high-weight topics get more questions)
- [ ] Past exam practice mode (similarity-weighted question selection)
- [ ] YouTube ingestion via yt-dlp (supplementary, non-canon flag)
- [ ] Class inheritance (link prior class as background context)
- [ ] **Export class** as `.yakclass` file
- [ ] **Import class** from `.yakclass` file (with merge/replace/cancel prompt)
- [ ] **Full backup** (zip all data + SQLite)
- [ ] 30-day backup reminder banner
- [ ] Export: quizzes as PDF, lecture summaries as PDF
- [ ] File cache view (per-class file library tab)
- [ ] Custom topic addition (user manually adds a block to the BRAIN file)

### Phase 5 — Polish (Weeks 17–20)
Goal: The app feels finished, tested, and ready to demo.

- [ ] Full onboarding flow refinement (with generated UI mockup screenshots using artifacts-builder)
- [ ] Settings screen (API key management, Whisper model selection, notification preferences, backup path, cost display)
- [ ] Performance dashboard (per-class topic heat map, accuracy trends over time)
- [ ] Class archival warnings (foundational course flag for declared major)
- [ ] Dark mode + light mode toggle
- [ ] Keyboard shortcuts (navigate classes, start recording, open chat)
- [ ] Loading states, empty states, error states throughout
- [ ] Cross-platform testing (Windows + Mac)
- [ ] App icon + splash screen + system tray icon
- [ ] Sidecar log viewer in Settings (for debugging)

---

## 15. Collaboration Split

| Area | Owner |
|---|---|
| React frontend — all screens | Avery |
| Tauri shell (Rust config, OS permissions, tray, sidecar lifecycle) | Avery |
| UI/UX design, component system, Tailwind theme | Avery |
| Onboarding flow + API key walkthrough | Avery |
| Syllabus confirmation modal (review + edit before saving) | Avery |
| Professor contact card + grading breakdown + schedule UI in Class Hub | Avery |
| Chat UI screen | Avery |
| Quiz UI (question display, hint system, results) | Avery |
| Study Mode + Recording overlay widget (frontend) | Avery |
| Search UI | Avery |
| Calendar view | Avery |
| Settings + cost display screen | Avery |
| Python FastAPI sidecar (server + routes) | Tommy |
| File ingestion pipeline (all file types) | Tommy |
| BRAIN.md builder + updater | Tommy |
| ChromaDB setup + embedding + retrieval | Tommy |
| Whisper integration (local, model management) | Tommy |
| GPT-4o / GPT-4o-mini API calls (all features) | Tommy |
| Chat engine (RAG-backed, history-aware) | Tommy |
| Semantic search engine | Tommy |
| Syllabus ingestion engine (full extraction, all tables) | Tommy |
| Syllabus update diff detection | Tommy |
| Grading weight → quiz generation weighting | Tommy |
| Duplicate detection | Tommy |
| YouTube ingestion (yt-dlp) | Tommy |
| Backup / export / import engine | Tommy |
| API cost logging + estimation | Tommy |
| Performance data aggregation | Tommy |
| Python unit tests | Tommy |
| SQLite schema design | **Both** |
| `shared/types/` API contract | **Both** |
| Integration tests | **Both** |
| GitHub Actions CI/CD setup | **Both** (do this Week 1) |

### Branching & PR Rules
- Branch strategy: `main` (stable) + feature branches (`feat/chat-ui`, `feat/whisper-pipeline`)
- No direct pushes to `main`
- Every PR requires one review from the other person before merge
- PR title format: `feat(scope): description` or `fix(scope): description`
- `shared/types/` changes require both people to sign off — it's the API contract

---

## 16. Future Business Notes

*(Parked — revisit after core functionality is complete and tested)*

- Pricing: $20/month — user brings their own OpenAI API key, subscription covers the app
- Auth system: Supabase (sign up, log in, log out) + optional cloud sync of BRAIN files and backups
- Distribution: Mac App Store + Windows Store + direct download (`.dmg` / `.msi`)
- Student verification: `.edu` email for potential discount
- App code signing: Mac notarization (Apple Developer Program, $99/yr) + Windows code signing certificate (~$300–500/yr from DigiCert or Sectigo) — required for clean installs without security warnings

---

## 17. Open Questions / Later Decisions

- **App icon + branding:** Design the YakAI logo. Should feel academic but modern — not a graduation cap.
- **Diagram generation format:** When the AI produces a circuit diagram or chart as part of a homework answer, the output is a rendered image. Still to decide: does YakAI use a structured diagram tool (Mermaid, D2) for reproducible output, or always rely on GPT-4o to describe and render ad-hoc? Structured tools are more editable; GPT-4o is more flexible.
- **Tablet/iPad support:** Tauri doesn't target iOS/Android. Students often use iPads in class. Out of scope for now — flag for post-v1.
- **Lecture note-taking during recording:** Should the user be able to type personal timestamped notes while recording that get merged into the transcript? Small feature but useful — consider for Phase 4.
- **Note export formats:** PDF is planned. Consider Markdown export for students using Obsidian or Notion. Low effort to add in Phase 4.
- **Multiple app users on same machine:** Currently designed single-user. If a roommate wants their own classes on the same laptop, the app would need user switching. Defer until after v1.
