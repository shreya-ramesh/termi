"""Ollama provider implementation for local model inference.

Talks to a local Ollama server over HTTP using ``requests``. This is the
only module in the codebase permitted to make direct HTTP calls to Ollama.
"""

from __future__ import annotations

import time

import requests

from termi.providers.base import BaseProvider, GenerationResult, Message
from termi.utils.exceptions import ProviderRequestError, ProviderResponseError
from termi.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "llama3.2"
DEFAULT_BASE_URL = "http://localhost:11434"
_TIMEOUT_SECONDS = 60


class OllamaProvider(BaseProvider):
    """LLM provider backed by a locally running Ollama server."""

    name = "ollama"

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        super().__init__(api_key=api_key, model=model)
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        """Ollama does not require an API key for local usage."""
        return True

    def generate(self, messages: list[Message]) -> GenerationResult:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": 0.2},
        }

        start = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise ProviderRequestError(
                f"Could not connect to Ollama at {self.base_url}. " "Is 'ollama serve' running?"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ProviderRequestError(f"Ollama request failed: {exc}") from exc
        elapsed = time.perf_counter() - start

        try:
            data = response.json()
            text = (data.get("message", {}).get("content") or "").strip()
        except ValueError as exc:
            raise ProviderResponseError("Ollama returned invalid JSON.") from exc

        if not text:
            raise ProviderResponseError("Ollama returned an empty response.")

        logger.debug("Ollama generation completed in %.3fs", elapsed)
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_seconds=elapsed,
            raw=data,
        )
