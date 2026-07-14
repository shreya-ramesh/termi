"""Groq provider implementation.

Uses Groq's OpenAI-compatible chat completions API. This is the only
module in the codebase permitted to import the ``groq`` SDK.
"""

from __future__ import annotations

import time

from termi.providers.base import BaseProvider, GenerationResult, Message
from termi.utils.exceptions import (
    ProviderAuthenticationError,
    ProviderRequestError,
    ProviderResponseError,
)
from termi.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(BaseProvider):
    """LLM provider backed by Groq's fast inference API."""

    name = "groq"

    def generate(self, messages: list[Message]) -> GenerationResult:
        try:
            from groq import APIStatusError, Groq
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderRequestError(
                "The 'groq' package is not installed. Run: pip install groq"
            ) from exc

        if not self.api_key:
            raise ProviderAuthenticationError("GROQ_API_KEY is not configured.")

        client = Groq(api_key=self.api_key)
        payload = [{"role": m.role, "content": m.content} for m in messages]

        start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=0.2,
            )
        except APIStatusError as exc:
            if exc.status_code in (401, 403):
                raise ProviderAuthenticationError(f"Groq authentication failed: {exc}") from exc
            raise ProviderRequestError(f"Groq request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network/SDK errors vary
            raise ProviderRequestError(f"Groq request failed: {exc}") from exc
        elapsed = time.perf_counter() - start

        if not response.choices:
            raise ProviderResponseError("Groq returned no choices.")

        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ProviderResponseError("Groq returned an empty response.")

        logger.debug("Groq generation completed in %.3fs", elapsed)
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_seconds=elapsed,
            raw=response,
        )
