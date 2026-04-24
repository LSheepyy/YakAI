# YakAI

AI-powered desktop study assistant. Add your class materials — lectures, textbooks, slides, recordings — and YakAI becomes a per-class AI expert scoped to exactly what was taught.

Built with Tauri (Rust + WebView) + React + TypeScript frontend, Python FastAPI sidecar.

## Project structure

```
yakai/
├── apps/desktop/          React + Tauri frontend
├── services/ai-core/      Python FastAPI sidecar
├── shared/types/          Shared TypeScript API types
└── .github/workflows/     CI (Python tests + frontend tests)
```

## Development

### Python sidecar

```bash
cd services/ai-core
pip install -r requirements.txt
uvicorn main:app --port 8765 --reload
```

The sidecar runs on `http://localhost:8765`. Set `YAKAI_APP_DATA` to control where data is stored (defaults to `~/.yakai`).

### React frontend (Vite dev server)

```bash
cd apps/desktop
npm install
npm run dev
```

Opens at `http://localhost:5173`. The frontend polls `localhost:8765/health` on startup — start the sidecar first.

### Desktop app (requires Rust)

Install Rust: https://rustup.rs

```bash
cd apps/desktop
npm install
npm run tauri dev
```

### Tests

```bash
# Python
cd services/ai-core && pytest tests/ -v

# Frontend
cd apps/desktop && npm test
```

## Phase 1 complete

- SQLite schema (all tables)
- Python FastAPI sidecar with health check, class/semester CRUD
- PDF ingestion (text extraction, classification, duplicate detection)
- BRAIN.md generation and update
- Syllabus extraction, persistence, and diff detection
- React frontend: onboarding, sidebar, Class Hub, file drop zone
- Vitest + pytest test suites

## Building the desktop binary

Rust must be installed. The Tauri build matrix (Windows + Mac) is configured in `.github/workflows/build.yml` but commented out pending code-signing certificate setup.
