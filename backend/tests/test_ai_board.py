from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai_board import ConversationMessage, build_ai_chat_prompt, parse_ai_chat_response  # noqa: E402
from app.ai_client import AIResponseError  # noqa: E402


def test_build_ai_chat_prompt_includes_board_and_history() -> None:
  prompt = build_ai_chat_prompt(
    {
      "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]}],
      "cards": {"card-1": {"id": "card-1", "title": "Test", "details": "Details"}},
    },
    [
      ConversationMessage(role="user", content="Move the card"),
      ConversationMessage(role="assistant", content="I can do that."),
    ],
    "Rename the column to Ideas.",
  )

  assert "Conversation history JSON:" in prompt
  assert "Current board JSON:" in prompt
  assert "Rename the column to Ideas." in prompt
  assert "Move the card" in prompt
  assert "I can do that." in prompt
  assert '"cardIds": [' in prompt


def test_parse_ai_chat_response_accepts_code_fenced_json() -> None:
  parsed = parse_ai_chat_response(
    """```json
    {
      \"assistant_message\": \"Updated the board.\",
      \"board_operations\": [
        {\"type\": \"rename_column\", \"column_id\": \"col-review\", \"title\": \"Ready\"},
        {\"type\": \"move_card\", \"card_id\": \"card-1\", \"column_id\": \"col-review\", \"position\": 0}
      ]
    }
    ```"""
  )

  assert parsed.assistant_message == "Updated the board."
  assert len(parsed.board_operations) == 2
  assert parsed.board_operations[0].type == "rename_column"
  assert parsed.board_operations[1].type == "move_card"


@pytest.mark.parametrize(
  "payload",
  [
    "not json",
    '{"board_operations": []}',
    '{"assistant_message": "ok", "board_operations": [{"type": "archive_card", "card_id": "card-1"}]}',
  ],
)
def test_parse_ai_chat_response_rejects_invalid_contract(payload: str) -> None:
  with pytest.raises(AIResponseError):
    parse_ai_chat_response(payload)