# Running Locally

## Part 3 integrated app

The current app runs as a single Docker container and serves:

- The statically exported Next.js Kanban app at `http://localhost:8000/`
- Example JSON API at `http://localhost:8000/api/hello`
- Health endpoint at `http://localhost:8000/api/health`

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

Integrated end-to-end tests:

```bash
cd frontend
npm run test:e2e
```