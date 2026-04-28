# Running Locally

## Part 3 integrated app

The current app runs as a single Docker container and serves:

- The statically exported Next.js Kanban app at `http://localhost:8000/`
- Example JSON API at `http://localhost:8000/api/hello`
- Health endpoint at `http://localhost:8000/api/health`
- Board API routes documented in `docs/BOARD_API.md`
- AI probe route at `POST http://localhost:8000/api/ai/probe`
- AI chat route at `POST http://localhost:8000/api/ai/chat`

The Part 4 login uses the fixed demo credentials below:

- Username: `user`
- Password: `password`

The Part 6 backend creates `db.sqlite3` automatically when the board API is first used.

The Part 8 AI probe route uses the fixed OpenRouter model `openai/gpt-oss-120b:free`.
Set `OPENROUTER_API_KEY` before calling that route for a real response.
If the key is missing, the backend returns a clear `503` error when the AI route is used.

The Part 9 board-aware AI route is documented in `docs/AI_API.md`.
It keeps chat history in backend memory for the current authenticated session and does not write that history to SQLite.

## Start and stop

Windows PowerShell:

```powershell
./scripts/start.ps1
./scripts/stop.ps1
```

macOS and Linux:

```bash
./scripts/start.sh
./scripts/stop.sh
```

## Manual Docker commands

```bash
docker build -t pm-mvp .
docker run --rm -p 8000:8000 --name pm-mvp pm-mvp
```

## Local test flow

Frontend unit tests:

```bash
cd frontend
npm run test:unit
```

Backend tests:

```bash
cd backend
uv run pytest
```

Opt-in live OpenRouter test:

```bash
cd backend
set OPENROUTER_API_KEY=your-key
set RUN_OPENROUTER_LIVE_TEST=1
uv run pytest tests/test_ai_live.py
```

Integrated end-to-end tests:

```bash
cd frontend
npm run test:e2e
```