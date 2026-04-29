from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.ai_board import ConversationStore
from app.ai_client import AIClient
from app.board_store import BoardStore
from app.config import (
  AUTH_USERNAME,
  SESSION_COOKIE_NAME,
  SESSION_MAX_AGE,
  is_test_api_enabled,
  resolve_db_path,
  resolve_frontend_dist_dir,
  resolve_session_secret,
)
from app.routers import ai, auth, board, health


def create_app(
  frontend_dist_dir: Path | None = None,
  db_path: Path | None = None,
  ai_client: AIClient | None = None,
) -> FastAPI:
  app = FastAPI(title="Project Management MVP Backend")

  app.state.board_store = BoardStore(resolve_db_path(db_path))
  app.state.board_store.initialize()
  app.state.conversation_store = ConversationStore()
  app.state.ai_client = ai_client

  app.add_middleware(
    SessionMiddleware,
    secret_key=resolve_session_secret(),
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
  )

  app.include_router(auth.router)
  app.include_router(board.router)
  app.include_router(ai.router)
  app.include_router(health.router)

  if is_test_api_enabled():
    test_router = APIRouter()

    @test_router.post("/api/test/reset-board", include_in_schema=False)
    def reset_board() -> dict[str, object]:
      return app.state.board_store.reset_board(AUTH_USERNAME)

    app.include_router(test_router)

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
