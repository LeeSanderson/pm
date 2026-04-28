import secrets
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.ai_board import (
  AIChatRequest,
  ConversationStore,
  build_ai_chat_prompt,
  parse_ai_chat_response,
  serialize_operations,
)

from app.ai_client import (
  OPENROUTER_PROBE_PROMPT,
  AIClient,
  AIConfigurationError,
  AIResponseError,
  resolve_ai_client,
)

from app.board_store import (
  BoardStore,
  BoardValidationError,
  CardNotFoundError,
  ColumnNotFoundError,
)

DEFAULT_FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "out"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "db.sqlite3"
AUTH_USERNAME = "user"
AUTH_PASSWORD = "password"
SESSION_COOKIE_NAME = "pm_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30
DEFAULT_SESSION_SECRET = "pm-mvp-dev-session-secret"
CHAT_SESSION_KEY = "chat_session_id"


class LoginRequest(BaseModel):
  username: str
  password: str


class RenameColumnRequest(BaseModel):
  title: str


class CreateCardRequest(BaseModel):
  title: str
  details: str = ""


class UpdateCardRequest(BaseModel):
  title: str
  details: str


class MoveCardRequest(BaseModel):
  column_id: str
  position: int


def resolve_frontend_dist_dir(frontend_dist_dir: Path | None = None) -> Path:
  if frontend_dist_dir is not None:
    return frontend_dist_dir

  configured_dir = os.environ.get("FRONTEND_DIST_DIR")
  if configured_dir:
    return Path(configured_dir)

  return DEFAULT_FRONTEND_DIST_DIR


def resolve_session_secret() -> str:
  return os.environ.get("SESSION_SECRET", DEFAULT_SESSION_SECRET)


def resolve_db_path(db_path: Path | None = None) -> Path:
  if db_path is not None:
    return db_path

  configured_path = os.environ.get("DB_PATH")
  if configured_path:
    return Path(configured_path)

  return DEFAULT_DB_PATH


def is_test_api_enabled() -> bool:
  return os.environ.get("ENABLE_TEST_API") == "1"


def get_authenticated_username(request: Request) -> str | None:
  username = request.session.get("username")
  if username == AUTH_USERNAME:
    return username
  return None


def require_authenticated_username(request: Request) -> str:
  username = get_authenticated_username(request)
  if username is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Not authenticated",
    )
  return username


def create_app(
  frontend_dist_dir: Path | None = None,
  db_path: Path | None = None,
  ai_client: AIClient | None = None,
) -> FastAPI:
  app = FastAPI(title="Project Management MVP Backend")
  board_store = BoardStore(resolve_db_path(db_path))
  conversation_store = ConversationStore()
  board_store.initialize()
  app.add_middleware(
    SessionMiddleware,
    secret_key=resolve_session_secret(),
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
  )

  @app.get("/api/auth/session")
  def read_session(request: Request) -> dict[str, str]:
    return {"username": require_authenticated_username(request)}

  @app.post("/api/auth/login")
  def login(payload: LoginRequest, request: Request) -> dict[str, str]:
    valid_username = secrets.compare_digest(payload.username, AUTH_USERNAME)
    valid_password = secrets.compare_digest(payload.password, AUTH_PASSWORD)
    if not (valid_username and valid_password):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
      )

    clear_conversation_history(request, conversation_store)
    request.session.clear()
    request.session["username"] = AUTH_USERNAME
    return {"username": AUTH_USERNAME}

  @app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
  def logout(request: Request) -> Response:
    clear_conversation_history(request, conversation_store)
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

  @app.get("/api/board")
  def read_board(request: Request) -> dict[str, object]:
    username = require_authenticated_username(request)
    return board_store.get_board(username)

  @app.post("/api/ai/probe")
  def probe_ai(request: Request) -> dict[str, str]:
    require_authenticated_username(request)

    try:
      active_ai_client = ai_client or resolve_ai_client()
      reply = active_ai_client.generate_text(OPENROUTER_PROBE_PROMPT)
    except AIConfigurationError as error:
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except AIResponseError as error:
      raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return {
      "model": active_ai_client.model,
      "prompt": OPENROUTER_PROBE_PROMPT,
      "reply": reply,
    }

  @app.post("/api/ai/chat")
  def chat_with_ai(payload: AIChatRequest, request: Request) -> dict[str, object]:
    username = require_authenticated_username(request)
    board = board_store.get_board(username)
    history_key = get_or_create_chat_session_id(request)
    prompt = build_ai_chat_prompt(
      board,
      conversation_store.get_messages(history_key),
      payload.message,
    )

    try:
      active_ai_client = ai_client or resolve_ai_client()
      raw_reply = active_ai_client.generate_text(prompt)
      parsed_reply = parse_ai_chat_response(raw_reply)
      operations = serialize_operations(parsed_reply.board_operations)
      next_board = board_store.apply_ai_operations(username, operations)
    except AIConfigurationError as error:
      raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except AIResponseError as error:
      raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except (BoardValidationError, ColumnNotFoundError, CardNotFoundError) as error:
      raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"AI response contained an invalid board operation: {error}",
      ) from error

    conversation_store.append_turn(history_key, payload.message, parsed_reply.assistant_message)
    return {
      "assistantMessage": parsed_reply.assistant_message,
      "appliedOperations": operations,
      "board": next_board,
      "model": active_ai_client.model,
    }

  if is_test_api_enabled():
    @app.post("/api/test/reset-board", include_in_schema=False)
    def reset_board() -> dict[str, object]:
      return board_store.reset_board(AUTH_USERNAME)

  @app.patch("/api/board/columns/{column_id}")
  def rename_column(
    column_id: str,
    payload: RenameColumnRequest,
    request: Request,
  ) -> dict[str, object]:
    username = require_authenticated_username(request)
    try:
      return board_store.rename_column(username, column_id, payload.title)
    except ColumnNotFoundError as error:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except BoardValidationError as error:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

  @app.post("/api/board/columns/{column_id}/cards")
  def create_card(
    column_id: str,
    payload: CreateCardRequest,
    request: Request,
  ) -> dict[str, object]:
    username = require_authenticated_username(request)
    try:
      return board_store.add_card(username, column_id, payload.title, payload.details)
    except ColumnNotFoundError as error:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except BoardValidationError as error:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

  @app.patch("/api/board/cards/{card_id}")
  def update_card(
    card_id: str,
    payload: UpdateCardRequest,
    request: Request,
  ) -> dict[str, object]:
    username = require_authenticated_username(request)
    try:
      return board_store.update_card(username, card_id, payload.title, payload.details)
    except CardNotFoundError as error:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except BoardValidationError as error:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

  @app.delete("/api/board/columns/{column_id}/cards/{card_id}")
  def delete_card(
    column_id: str,
    card_id: str,
    request: Request,
  ) -> dict[str, object]:
    username = require_authenticated_username(request)
    try:
      return board_store.delete_card(username, column_id, card_id)
    except CardNotFoundError as error:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

  @app.patch("/api/board/cards/{card_id}/move")
  def move_card(
    card_id: str,
    payload: MoveCardRequest,
    request: Request,
  ) -> dict[str, object]:
    username = require_authenticated_username(request)
    try:
      return board_store.move_card(
        username,
        card_id,
        payload.column_id,
        payload.position,
      )
    except (ColumnNotFoundError, CardNotFoundError) as error:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except BoardValidationError as error:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

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


def clear_conversation_history(request: Request, conversation_store: ConversationStore) -> None:
  history_key = request.session.get(CHAT_SESSION_KEY)
  if isinstance(history_key, str) and history_key:
    conversation_store.clear(history_key)


def get_or_create_chat_session_id(request: Request) -> str:
  history_key = request.session.get(CHAT_SESSION_KEY)
  if isinstance(history_key, str) and history_key:
    return history_key

  history_key = secrets.token_urlsafe(16)
  request.session[CHAT_SESSION_KEY] = history_key
  return history_key


