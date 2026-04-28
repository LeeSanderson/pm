from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.ai_client import AIResponseError

MAX_CONVERSATION_MESSAGES = 12


def _normalize_required_text(value: str, message: str) -> str:
  normalized = value.strip()
  if not normalized:
    raise ValueError(message)
  return normalized


class ConversationMessage(BaseModel):
  role: Literal["user", "assistant"]
  content: str

  @field_validator("content")
  @classmethod
  def validate_content(cls, value: str) -> str:
    return _normalize_required_text(value, "Conversation content is required")


class AIChatRequest(BaseModel):
  message: str

  @field_validator("message")
  @classmethod
  def validate_message(cls, value: str) -> str:
    return _normalize_required_text(value, "Message is required")


class RenameColumnOperation(BaseModel):
  type: Literal["rename_column"]
  column_id: str
  title: str

  @field_validator("column_id", "title")
  @classmethod
  def validate_required_text(cls, value: str) -> str:
    return _normalize_required_text(value, "Operation field is required")


class CreateCardOperation(BaseModel):
  type: Literal["create_card"]
  column_id: str
  title: str
  details: str = ""

  @field_validator("column_id", "title")
  @classmethod
  def validate_required_text(cls, value: str) -> str:
    return _normalize_required_text(value, "Operation field is required")


class UpdateCardOperation(BaseModel):
  type: Literal["update_card"]
  card_id: str
  title: str
  details: str

  @field_validator("card_id", "title")
  @classmethod
  def validate_required_text(cls, value: str) -> str:
    return _normalize_required_text(value, "Operation field is required")


class MoveCardOperation(BaseModel):
  type: Literal["move_card"]
  card_id: str
  column_id: str
  position: int

  @field_validator("card_id", "column_id")
  @classmethod
  def validate_required_text(cls, value: str) -> str:
    return _normalize_required_text(value, "Operation field is required")


class DeleteCardOperation(BaseModel):
  type: Literal["delete_card"]
  card_id: str

  @field_validator("card_id")
  @classmethod
  def validate_required_text(cls, value: str) -> str:
    return _normalize_required_text(value, "Operation field is required")


BoardOperation = Annotated[
  RenameColumnOperation
  | CreateCardOperation
  | UpdateCardOperation
  | MoveCardOperation
  | DeleteCardOperation,
  Field(discriminator="type"),
]


class AIChatModelResponse(BaseModel):
  assistant_message: str
  board_operations: list[BoardOperation] = Field(default_factory=list)

  @field_validator("assistant_message")
  @classmethod
  def validate_assistant_message(cls, value: str) -> str:
    return _normalize_required_text(value, "assistant_message is required")


class ConversationStore:
  def __init__(self, max_messages: int = MAX_CONVERSATION_MESSAGES):
    self.max_messages = max_messages
    self._messages: dict[str, list[ConversationMessage]] = {}

  def get_messages(self, session_id: str) -> list[ConversationMessage]:
    return list(self._messages.get(session_id, []))

  def append_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
    history = self._messages.setdefault(session_id, [])
    history.extend(
      [
        ConversationMessage(role="user", content=user_message),
        ConversationMessage(role="assistant", content=assistant_message),
      ]
    )
    self._messages[session_id] = history[-self.max_messages :]

  def clear(self, session_id: str) -> None:
    self._messages.pop(session_id, None)


def build_ai_chat_prompt(
  board: dict[str, object],
  conversation_history: Sequence[ConversationMessage],
  user_message: str,
) -> str:
  history_payload = [message.model_dump() for message in conversation_history]
  return "\n".join(
    [
      "You are the AI assistant for a project management kanban board.",
      "Return valid JSON only. Do not include markdown, code fences, or explanatory text outside the JSON object.",
      "Use this exact response schema:",
      '{"assistant_message":"string","board_operations":[{"type":"rename_column","column_id":"string","title":"string"}|{"type":"create_card","column_id":"string","title":"string","details":"string"}|{"type":"update_card","card_id":"string","title":"string","details":"string"}|{"type":"move_card","card_id":"string","column_id":"string","position":0}|{"type":"delete_card","card_id":"string"}]}',
      "Rules:",
      "- Use an empty board_operations array when no board change is needed.",
      "- Only reference column_id and card_id values that already exist in the current board.",
      "- For create_card, do not invent a card id. The backend will generate it.",
      "- position is zero-based and is the final index inside the target column.",
      "- If the user explicitly asks for no board changes, keep board_operations empty.",
      "- If the request is ambiguous or impossible, explain that in assistant_message and keep board_operations empty.",
      "Conversation history JSON:",
      json.dumps(history_payload, indent=2, sort_keys=True),
      "Current board JSON:",
      json.dumps(board, indent=2, sort_keys=True),
      "Latest user request:",
      user_message.strip(),
    ]
  )


def parse_ai_chat_response(raw_response: str) -> AIChatModelResponse:
  normalized = _strip_code_fences(raw_response)
  if not normalized.startswith("{"):
    raise AIResponseError("AI response did not match the required JSON contract")

  try:
    return AIChatModelResponse.model_validate_json(normalized)
  except ValidationError as error:
    raise AIResponseError("AI response did not match the required JSON contract") from error
  except json.JSONDecodeError as error:
    raise AIResponseError("AI response was not valid JSON") from error


def serialize_operations(operations: Sequence[BoardOperation]) -> list[dict[str, object]]:
  return [operation.model_dump() for operation in operations]


def _strip_code_fences(raw_response: str) -> str:
  normalized = raw_response.strip()
  if not normalized.startswith("```"):
    return normalized

  if not normalized.endswith("```"):
    return normalized

  normalized = normalized[3:-3].strip()
  if normalized.lower().startswith("json"):
    normalized = normalized[4:].strip()
  return normalized