import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.ai_board import ConversationStore
from app.config import AUTH_PASSWORD, AUTH_USERNAME
from app.dependencies import (
  clear_conversation_history,
  get_conversation_store,
  require_authenticated_username,
)
from app.models import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/session")
def read_session(username: str = Depends(require_authenticated_username)) -> dict[str, str]:
  return {"username": username}


@router.post("/login")
def login(
  payload: LoginRequest,
  request: Request,
  conversation_store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, str]:
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
  request: Request,
  conversation_store: ConversationStore = Depends(get_conversation_store),
) -> Response:
  clear_conversation_history(request, conversation_store)
  request.session.clear()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
