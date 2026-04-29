from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai_client import DummyAIClient
from tests.conftest import FailingAIClient, RecordingAIClient


def test_ai_probe_requires_login(client: TestClient) -> None:
  response = client.post("/api/ai/probe")

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_ai_chat_requires_login(client: TestClient) -> None:
  response = client.post("/api/ai/chat", json={"message": "Hello"})

  assert response.status_code == 401
  assert response.json() == {"detail": "Not authenticated"}


def test_ai_probe_returns_dummy_response(make_authenticated_client, tmp_path: Path) -> None:
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=DummyAIClient("4"),
  )

  response = client.post("/api/ai/probe")

  assert response.status_code == 200
  assert response.json() == {
    "model": "dummy/openrouter-probe",
    "prompt": "What is 2+2? Reply with digits only.",
    "reply": "4",
  }


def test_ai_chat_returns_noop_reply_and_current_board(
  make_authenticated_client, tmp_path: Path
) -> None:
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=DummyAIClient('{"assistant_message": "No changes needed.", "board_operations": []}'),
  )

  response = client.post("/api/ai/chat", json={"message": "Just acknowledge this."})

  assert response.status_code == 200
  payload = response.json()
  assert payload["assistantMessage"] == "No changes needed."
  assert payload["appliedOperations"] == []
  assert payload["board"]["columns"][0]["id"] == "col-backlog"
  assert payload["board"]["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_ai_probe_requires_configured_api_key(
  make_authenticated_client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
  monkeypatch.delenv("OPENROUTER_USE_DUMMY", raising=False)
  client = make_authenticated_client(db_path=tmp_path / "db.sqlite3")

  response = client.post("/api/ai/probe")

  assert response.status_code == 503
  assert response.json() == {"detail": "OPENROUTER_API_KEY is not set"}


def test_ai_chat_requires_configured_api_key(
  make_authenticated_client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
  monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
  monkeypatch.delenv("OPENROUTER_USE_DUMMY", raising=False)
  client = make_authenticated_client(db_path=tmp_path / "db.sqlite3")

  response = client.post("/api/ai/chat", json={"message": "Hello"})

  assert response.status_code == 503
  assert response.json() == {"detail": "OPENROUTER_API_KEY is not set"}


def test_ai_probe_maps_upstream_failures_to_bad_gateway(
  make_authenticated_client, tmp_path: Path
) -> None:
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=FailingAIClient(),
  )

  response = client.post("/api/ai/probe")

  assert response.status_code == 502
  assert response.json() == {"detail": "OpenRouter request failed"}


def test_ai_chat_records_conversation_history_in_session_memory(
  make_authenticated_client, tmp_path: Path
) -> None:
  ai_client = RecordingAIClient(
    [
      '{"assistant_message": "First reply", "board_operations": []}',
      '{"assistant_message": "Second reply", "board_operations": []}',
    ]
  )
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=ai_client,
  )

  first_response = client.post("/api/ai/chat", json={"message": "First request"})
  second_response = client.post("/api/ai/chat", json={"message": "Second request"})

  assert first_response.status_code == 200
  assert second_response.status_code == 200
  assert len(ai_client.prompts) == 2
  assert "First request" in ai_client.prompts[1]
  assert "First reply" in ai_client.prompts[1]
  assert "Second request" in ai_client.prompts[1]


def test_ai_chat_applies_multiple_board_operations(
  make_authenticated_client, tmp_path: Path
) -> None:
  response_payload = """{
    "assistant_message": "Updated the board.",
    "board_operations": [
      {"type": "rename_column", "column_id": "col-review", "title": "Ready"},
      {"type": "update_card", "card_id": "card-1", "title": "Align roadmap themes and owners", "details": "Add owners and due dates."},
      {"type": "move_card", "card_id": "card-1", "column_id": "col-review", "position": 0},
      {"type": "create_card", "column_id": "col-backlog", "title": "Schedule roadmap review", "details": "Book time with design and engineering leads."}
    ]
  }"""
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=DummyAIClient(response_payload),
  )

  response = client.post("/api/ai/chat", json={"message": "Update the roadmap work."})

  assert response.status_code == 200
  payload = response.json()
  assert payload["assistantMessage"] == "Updated the board."
  assert payload["board"]["columns"][3]["title"] == "Ready"
  assert payload["board"]["columns"][3]["cardIds"][0] == "card-1"
  assert payload["board"]["cards"]["card-1"] == {
    "id": "card-1",
    "title": "Align roadmap themes and owners",
    "details": "Add owners and due dates.",
  }
  created_cards = [
    card for card in payload["board"]["cards"].values()
    if card["title"] == "Schedule roadmap review"
  ]
  assert len(created_cards) == 1
  created_card_id = created_cards[0]["id"]
  assert created_card_id in payload["board"]["columns"][0]["cardIds"]


def test_ai_chat_rejects_invalid_model_output_without_partial_board_changes(
  make_authenticated_client, tmp_path: Path
) -> None:
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=DummyAIClient(
      '{"assistant_message": "Tried to update the board.", "board_operations": ['
      '{"type": "rename_column", "column_id": "col-review", "title": "Ready"},'
      '{"type": "move_card", "card_id": "card-1", "column_id": "col-review", "position": 99}'
      "]}"
    ),
  )
  before_response = client.get("/api/board")

  response = client.post("/api/ai/chat", json={"message": "Make impossible changes."})
  after_response = client.get("/api/board")

  assert before_response.status_code == 200
  assert response.status_code == 502
  assert response.json() == {
    "detail": "AI response contained an invalid board operation: Position is out of range"
  }
  assert after_response.status_code == 200
  assert after_response.json() == before_response.json()


def test_ai_chat_rejects_blank_message(make_authenticated_client, tmp_path: Path) -> None:
  client = make_authenticated_client(
    db_path=tmp_path / "db.sqlite3",
    ai_client=DummyAIClient("{}"),
  )

  response = client.post("/api/ai/chat", json={"message": ""})

  assert response.status_code == 422
