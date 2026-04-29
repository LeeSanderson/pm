from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.ai_board import (
  AIChatRequest,
  ConversationStore,
  build_ai_chat_prompt,
  parse_ai_chat_response,
  serialize_operations,
)
from app.ai_client import AIClient, AIResponseError, OPENROUTER_PROBE_PROMPT
from app.board_store import BoardStore, BoardValidationError, CardNotFoundError, ColumnNotFoundError
from app.dependencies import (
  get_ai_client,
  get_board_store,
  get_conversation_store,
  get_or_create_chat_session_id,
  require_authenticated_username,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/probe")
def probe_ai(
  _username: str = Depends(require_authenticated_username),
  ai_client: AIClient = Depends(get_ai_client),
) -> dict[str, str]:
  try:
    reply = ai_client.generate_text(OPENROUTER_PROBE_PROMPT)
  except AIResponseError as error:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
  return {
    "model": ai_client.model,
    "prompt": OPENROUTER_PROBE_PROMPT,
    "reply": reply,
  }


@router.post("/chat")
def chat_with_ai(
  payload: AIChatRequest,
  request: Request,
  username: str = Depends(require_authenticated_username),
  board_store: BoardStore = Depends(get_board_store),
  conversation_store: ConversationStore = Depends(get_conversation_store),
  ai_client: AIClient = Depends(get_ai_client),
) -> dict[str, object]:
  board = board_store.get_board(username)
  history_key = get_or_create_chat_session_id(request)
  prompt = build_ai_chat_prompt(
    board,
    conversation_store.get_messages(history_key),
    payload.message,
  )
  try:
    raw_reply = ai_client.generate_text(prompt)
    parsed_reply = parse_ai_chat_response(raw_reply)
    operations = serialize_operations(parsed_reply.board_operations)
    next_board = board_store.apply_ai_operations(username, operations)
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
    "model": ai_client.model,
  }
