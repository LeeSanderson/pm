import secrets

from fastapi import HTTPException, Request, status

from app.ai_board import ConversationStore
from app.ai_client import AIClient, AIConfigurationError, resolve_ai_client
from app.board_store import BoardStore
from app.config import AUTH_USERNAME, CHAT_SESSION_KEY


def get_board_store(request: Request) -> BoardStore:
  return request.app.state.board_store


def get_conversation_store(request: Request) -> ConversationStore:
  return request.app.state.conversation_store


def get_ai_client(request: Request) -> AIClient:
  override: AIClient | None = getattr(request.app.state, "ai_client", None)
  if override is not None:
    return override
  try:
    return resolve_ai_client()
  except AIConfigurationError as error:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


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


def get_or_create_chat_session_id(request: Request) -> str:
  history_key = request.session.get(CHAT_SESSION_KEY)
  if isinstance(history_key, str) and history_key:
    return history_key
  history_key = secrets.token_urlsafe(16)
  request.session[CHAT_SESSION_KEY] = history_key
  return history_key


def clear_conversation_history(request: Request, conversation_store: ConversationStore) -> None:
  history_key = request.session.get(CHAT_SESSION_KEY)
  if isinstance(history_key, str) and history_key:
    conversation_store.clear(history_key)
