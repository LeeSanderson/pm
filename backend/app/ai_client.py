from __future__ import annotations

import os
from collections.abc import Callable
from typing import Protocol

import httpx

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
OPENROUTER_PROBE_PROMPT = "What is 2+2? Reply with digits only."
OPENROUTER_TIMEOUT_SECONDS = 30.0


class AIClientError(Exception):
  pass


class AIConfigurationError(AIClientError):
  pass


class AIResponseError(AIClientError):
  pass


class AIClient(Protocol):
  model: str

  def generate_text(self, prompt: str) -> str:
    ...


class DummyAIClient:
  def __init__(self, response_text: str = "4"):
    self.model = "dummy/openrouter-probe"
    self._response_text = response_text

  def generate_text(self, prompt: str) -> str:
    return self._response_text


class OpenRouterClient:
  def __init__(
    self,
    api_key: str,
    model: str = OPENROUTER_MODEL,
    post: Callable[..., httpx.Response] | None = None,
  ):
    self.api_key = api_key
    self.model = model
    self._post = post or httpx.post

  def generate_text(self, prompt: str) -> str:
    try:
      response = self._post(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        headers={
          "Authorization": f"Bearer {self.api_key}",
          "Content-Type": "application/json",
          "X-OpenRouter-Title": "Project Management MVP",
        },
        json={
          "model": self.model,
          "messages": [{"role": "user", "content": prompt}],
        },
        timeout=OPENROUTER_TIMEOUT_SECONDS,
      )
      response.raise_for_status()
    except httpx.HTTPError as error:
      raise AIResponseError("OpenRouter request failed") from error

    try:
      payload = response.json()
      choice = payload["choices"][0]
      error_payload = choice.get("error")
      if isinstance(error_payload, dict):
        message = error_payload.get("message")
        raise AIResponseError(message or "OpenRouter returned an error")

      content = choice["message"]["content"]
    except AIResponseError:
      raise
    except (IndexError, KeyError, TypeError, ValueError) as error:
      raise AIResponseError("OpenRouter response did not include assistant content") from error

    if not isinstance(content, str) or not content.strip():
      raise AIResponseError("OpenRouter response did not include assistant content")

    return content.strip()


def resolve_openrouter_api_key() -> str:
  api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
  if not api_key:
    raise AIConfigurationError("OPENROUTER_API_KEY is not set")
  return api_key


def resolve_ai_client() -> AIClient:
  if os.environ.get("OPENROUTER_USE_DUMMY") == "1":
    return DummyAIClient(os.environ.get("OPENROUTER_DUMMY_RESPONSE", "4"))

  return OpenRouterClient(resolve_openrouter_api_key())