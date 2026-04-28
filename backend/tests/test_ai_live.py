import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai_client import OPENROUTER_MODEL  # noqa: E402
from app.main import create_app  # noqa: E402


pytestmark = pytest.mark.skipif(
  os.environ.get("RUN_OPENROUTER_LIVE_TEST") != "1",
  reason="Set RUN_OPENROUTER_LIVE_TEST=1 to run the live OpenRouter integration test.",
)


def test_openrouter_live_probe(tmp_path: Path) -> None:
  if not os.environ.get("OPENROUTER_API_KEY", "").strip():
    pytest.skip("OPENROUTER_API_KEY is required for the live OpenRouter test.")

  client = TestClient(create_app(tmp_path / "missing", db_path=tmp_path / "db.sqlite3"))
  login_response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )
  assert login_response.status_code == 200

  response = client.post("/api/ai/probe")

  assert response.status_code == 200
  payload = response.json()
  assert payload["model"] == OPENROUTER_MODEL
  assert payload["prompt"] == "What is 2+2? Reply with digits only."
  assert "4" in payload["reply"]


def test_openrouter_live_chat_noop(tmp_path: Path) -> None:
  if not os.environ.get("OPENROUTER_API_KEY", "").strip():
    pytest.skip("OPENROUTER_API_KEY is required for the live OpenRouter test.")

  client = TestClient(create_app(tmp_path / "missing", db_path=tmp_path / "db.sqlite3"))
  login_response = client.post(
    "/api/auth/login",
    json={"username": "user", "password": "password"},
  )
  assert login_response.status_code == 200

  board_response = client.get("/api/board")
  assert board_response.status_code == 200

  response = client.post(
    "/api/ai/chat",
    json={
      "message": "Reply with a brief acknowledgement only. Do not change the board. board_operations must be an empty array.",
    },
  )

  assert response.status_code == 200
  payload = response.json()
  assert payload["model"] == OPENROUTER_MODEL
  assert payload["assistantMessage"]
  assert payload["appliedOperations"] == []
  assert payload["board"] == board_response.json()