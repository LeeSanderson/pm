# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Kanban project management MVP with AI chat integration. FastAPI backend (Python) serves a statically-exported Next.js frontend from a single Docker container on port 8000.

## Commands

### Backend (run from `backend/`)
```bash
uv run pytest                   # All backend tests
uv run pytest tests/test_app.py # Single test file
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Dev server
```

### Frontend (run from `frontend/`)
```bash
npm run dev          # Dev server on :3000 (proxies API to :8000)
npm run build        # Static export to ./out
npm run test:unit    # Vitest unit tests
npm run test:e2e     # Playwright e2e tests (requires running app)
npm run test:all     # Both unit and e2e
npm run lint         # ESLint
```

### Docker (run from project root)
```bash
./scripts/start.ps1  # Windows: build and run container on :8000
./scripts/stop.ps1   # Windows: stop container
./scripts/start.sh   # macOS/Linux equivalent
docker build -t pm-mvp . && docker run --rm -p 8000:8000 --env-file .env pm-mvp
```

## Architecture

### Request Flow
The frontend is a static export (`frontend/out/`) served by FastAPI's `StaticFiles`. All API routes are prefixed `/api/`. When running locally, `npm run dev` proxies `/api/*` to the backend at `:8000`.

### Authentication
Signed HTTP-only cookie (`pm_session`) with 30-day TTL. Hardcoded credentials: `user` / `password`. `GET /api/auth/session` is called on mount to check auth state; 401 shows LoginForm, 200 shows KanbanBoard.

### Board State
Each API mutation returns the **full board aggregate** — the frontend replaces its entire local state with the response rather than merging. Board shape: `{columns: Column[], cards: Record<string, Card>}`.

Database uses a normalized relational schema (SQLite): `users` → `boards` → `columns` + `cards`. The board aggregate is reconstructed at read time. Users and boards are auto-created on first access.

### AI Chat
`POST /api/ai/chat` fetches the current board from SQLite, appends to in-memory session history, calls OpenRouter (`openai/gpt-oss-120b:free`), parses the JSON response (must contain `assistant_message` + `board_operations`), applies operations atomically, and returns the updated board. Chat history is **not persisted** — it lives in a Python dict keyed by session ID and is cleared on logout or server restart.

### Key Files
- `backend/app/main.py` — FastAPI app, all routes, middleware, static file serving
- `backend/app/board_store.py` — all SQLite reads/writes, board aggregate reconstruction
- `backend/app/ai_client.py` — OpenRouter HTTP client abstraction
- `backend/app/ai_board.py` — AI prompt construction, response parsing, operation validation
- `frontend/src/components/KanbanApp.tsx` — auth state gate, top-level wrapper
- `frontend/src/components/KanbanBoard.tsx` — board UI, drag-and-drop, API calls
- `frontend/src/components/AIChatSidebar.tsx` — AI chat UI, operation display
- `frontend/src/lib/boardApi.ts` — all frontend API client functions

## Environment Variables

`.env` at project root (copied into Docker container via `--env-file`):
- `OPENROUTER_API_KEY` — required for AI routes; absence causes 503
- `SESSION_SECRET` — signed cookie secret (defaults to hardcoded dev value)
- `DB_PATH` — SQLite file path (default: `db.sqlite3`)
- `FRONTEND_DIST_DIR` — path to Next.js export (default: `/app/frontend-out` in Docker)
- `ENABLE_TEST_API=1` — exposes `/api/test/reset-board` endpoint
- `OPENROUTER_USE_DUMMY=1` — bypasses real OpenRouter calls (for testing)

## Testing Notes

- `ENABLE_TEST_API=1` must be set for backend tests that reset board state
- `OPENROUTER_USE_DUMMY=1` is used in most backend tests; `RUN_OPENROUTER_LIVE_TEST=1` enables live calls
- E2E tests (`frontend/tests/`) require the app to be running on `:8000`
