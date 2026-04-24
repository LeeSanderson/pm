import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

DEFAULT_FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"


def resolve_frontend_dist_dir(frontend_dist_dir: Path | None = None) -> Path:
  if frontend_dist_dir is not None:
    return frontend_dist_dir

  configured_dir = os.environ.get("FRONTEND_DIST_DIR")
  if configured_dir:
    return Path(configured_dir)

  return DEFAULT_FRONTEND_DIST_DIR


def create_app(frontend_dist_dir: Path | None = None) -> FastAPI:
  app = FastAPI(title="Project Management MVP Backend")

  @app.get("/api/health")
  def read_health() -> dict[str, str]:
    return {"status": "ok"}

  @app.get("/api/hello")
  def read_hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI."}

  dist_dir = resolve_frontend_dist_dir(frontend_dist_dir)
  if dist_dir.exists():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
  else:
    @app.get("/", response_class=PlainTextResponse, include_in_schema=False)
    def read_missing_frontend() -> PlainTextResponse:
      return PlainTextResponse(
        "Frontend build not found. Run `npm run build` in frontend/ or use the Docker image.",
        status_code=503,
      )

  return app


app = create_app()


