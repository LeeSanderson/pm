# Running Locally

## Part 2 scaffold

The current scaffold runs as a single Docker container and serves:

- Temporary HTML at `http://localhost:8000/`
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