import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai_client import AIResponseError, OPENROUTER_MODEL, DummyAIClient  # noqa: E402
from app.main import create_app  # noqa: E402


class FailingAIClient:
  model = OPENROUTER_MODEL

  def generate_text(self, prompt: str) -> str:
    raise AIResponseError("OpenRouter request failed")


class RecordingAIClient:
  model = "dummy/openrouter-chat"

  def __init__(self, responses: list[str]):
    self._responses = responses
    self.prompts: list[str] = []

  def generate_text(self, prompt: str) -> str:
    self.prompts.append(prompt)
    if not self._responses:
      raise AssertionError("No AI response queued for test")
    return self._responses.pop(0)


@pytest.fixture
def make_client(tmp_path: Path):
  """Factory fixture: creates a TestClient with no authentication."""
  def _inner(db_path: Path | None = None, ai_client=None) -> TestClient:
    return TestClient(
      create_app(
        frontend_dist_dir=tmp_path / "missing",
        db_path=db_path,
        ai_client=ai_client,
      )
    )
  return _inner


@pytest.fixture
def make_authenticated_client(make_client):
  """Factory fixture: creates a TestClient pre-authenticated as 'user'."""
  def _inner(db_path: Path | None = None, ai_client=None) -> TestClient:
    client = make_client(db_path=db_path, ai_client=ai_client)
    response = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    return client
  return _inner


@pytest.fixture
def client(make_client, tmp_path: Path) -> TestClient:
  """Unauthenticated TestClient with a default DummyAIClient."""
  return make_client(db_path=tmp_path / "db.sqlite3", ai_client=DummyAIClient())


@pytest.fixture
def auth_client(make_authenticated_client, tmp_path: Path) -> TestClient:
  """Authenticated TestClient with a default DummyAIClient."""
  return make_authenticated_client(db_path=tmp_path / "db.sqlite3", ai_client=DummyAIClient())
