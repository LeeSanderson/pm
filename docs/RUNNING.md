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

## AI sidebar usage

After signing in, the board page includes an AI sidebar.

- Type a request such as moving a card, adding a card, or renaming a column.
- Click `Send` and wait for the assistant reply.
- If the AI returns board operations, the UI replaces the current board state with the backend response automatically.
- If the AI returns no board changes, the assistant reply still appears and the board stays as-is.

Current MVP limits:

- Chat history is only kept in backend memory for the current session.
- Chat history is cleared on logout or backend restart.
- The sidebar does not yet support retrying or editing a previous AI prompt in place.
- Existing manual board edits and AI submissions are serialized; while one is in flight, the other interactions wait.

## Start and stop

Windows PowerShell:

```powershell
./scripts/start.ps1
./scripts/stop.ps1
```

If a root `.env` file exists, the start script passes it into the container automatically.

macOS and Linux:

```bash
./scripts/start.sh
./scripts/stop.sh
```

## Manual Docker commands

```bash
docker build -t pm-mvp .
docker run --rm -p 8000:8000 --env-file .env --name pm-mvp pm-mvp
```

If you omit `--env-file .env`, AI routes will return `OPENROUTER_API_KEY is not set`.

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