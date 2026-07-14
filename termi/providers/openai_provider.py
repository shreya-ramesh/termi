"""OpenAI provider implementation.

This is the only module in the codebase permitted to import the
``openai`` SDK.
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

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseProvider):
    """LLM provider backed by the OpenAI Chat Completions API."""

    name = "openai"

    def generate(self, messages: list[Message]) -> GenerationResult:
        try:
            from openai import APIStatusError, AuthenticationError, OpenAI
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderRequestError(
                "The 'openai' package is not installed. Run: pip install openai"
            ) from exc

        if not self.api_key:
            raise ProviderAuthenticationError("OPENAI_API_KEY is not configured.")

        client = OpenAI(api_key=self.api_key)
        payload = [{"role": m.role, "content": m.content} for m in messages]

        start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=0.2,
            )
        except AuthenticationError as exc:
            raise ProviderAuthenticationError(f"OpenAI authentication failed: {exc}") from exc
        except APIStatusError as exc:
            raise ProviderRequestError(f"OpenAI request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network/SDK errors vary
            raise ProviderRequestError(f"OpenAI request failed: {exc}") from exc
        elapsed = time.perf_counter() - start

        if not response.choices:
            raise ProviderResponseError("OpenAI returned no choices.")

        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ProviderResponseError("OpenAI returned an empty response.")

        logger.debug("OpenAI generation completed in %.3fs", elapsed)
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_seconds=elapsed,
            raw=response,
        )
