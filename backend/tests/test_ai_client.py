from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai_client import (  # noqa: E402
  AIConfigurationError,
  AIResponseError,
  DummyAIClient,
  OPENROUTER_CHAT_COMPLETIONS_URL,
  OPENROUTER_MODEL,
  OpenRouterClient,
  resolve_ai_client,
)


def test_resolve_ai_client_requires_api_key_when_dummy_disabled(monkeypatch) -> None:
  monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
  monkeypatch.delenv("OPENROUTER_USE_DUMMY", raising=False)

  with pytest.raises(AIConfigurationError, match="OPENROUTER_API_KEY is not set"):
    resolve_ai_client()


def test_resolve_ai_client_returns_dummy_client_when_enabled(monkeypatch) -> None:
  monkeypatch.setenv("OPENROUTER_USE_DUMMY", "1")
  monkeypatch.setenv("OPENROUTER_DUMMY_RESPONSE", "4")

  client = resolve_ai_client()

  assert isinstance(client, DummyAIClient)
  assert client.generate_text("ignored") == "4"


def test_openrouter_client_parses_assistant_content_from_response() -> None:
  def fake_post(*args, **kwargs) -> httpx.Response:
    assert args[0] == OPENROUTER_CHAT_COMPLETIONS_URL
    assert kwargs["json"]["model"] == OPENROUTER_MODEL
    return httpx.Response(
      200,
      json={
        "choices": [
          {
            "message": {
              "role": "assistant",
              "content": "4",
            }
          }
        ]
      },
      request=httpx.Request("POST", OPENROUTER_CHAT_COMPLETIONS_URL),
    )

  client = OpenRouterClient(api_key="test-key", post=fake_post)

  assert client.generate_text("What is 2+2?") == "4"


def test_openrouter_client_rejects_malformed_responses() -> None:
  def fake_post(*args, **kwargs) -> httpx.Response:
    return httpx.Response(
      200,
      json={"choices": []},
      request=httpx.Request("POST", OPENROUTER_CHAT_COMPLETIONS_URL),
    )

  client = OpenRouterClient(api_key="test-key", post=fake_post)

  with pytest.raises(AIResponseError, match="assistant content"):
    client.generate_text("What is 2+2?")


def test_openrouter_client_maps_http_errors_to_response_errors() -> None:
  def fake_post(*args, **kwargs) -> httpx.Response:
    return httpx.Response(
      502,
      json={"detail": "upstream failed"},
      request=httpx.Request("POST", OPENROUTER_CHAT_COMPLETIONS_URL),
    )

  client = OpenRouterClient(api_key="test-key", post=fake_post)

  with pytest.raises(AIResponseError, match="OpenRouter request failed"):
    client.generate_text("What is 2+2?")