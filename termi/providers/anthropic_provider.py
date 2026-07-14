"""Anthropic Claude provider implementation.

This is the only module in the codebase permitted to import the
``anthropic`` SDK.
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

DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_MAX_TOKENS = 1024


class AnthropicProvider(BaseProvider):
    """LLM provider backed by the Anthropic Messages API."""

    name = "anthropic"

    def generate(self, messages: list[Message]) -> GenerationResult:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderRequestError(
                "The 'anthropic' package is not installed. " "Run: pip install anthropic"
            ) from exc

        if not self.api_key:
            raise ProviderAuthenticationError("ANTHROPIC_API_KEY is not configured.")

        client = anthropic.Anthropic(api_key=self.api_key)

        system_parts = [m.content for m in messages if m.role == "system"]
        conversation = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]

        start = time.perf_counter()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=_DEFAULT_MAX_TOKENS,
                system="\n".join(system_parts) if system_parts else anthropic.NOT_GIVEN,
                messages=conversation,
                temperature=0.2,
            )
        except anthropic.AuthenticationError as exc:
            raise ProviderAuthenticationError(f"Anthropic authentication failed: {exc}") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderRequestError(f"Anthropic request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network/SDK errors vary
            raise ProviderRequestError(f"Anthropic request failed: {exc}") from exc
        elapsed = time.perf_counter() - start

        text_blocks = [
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ]
        text = "".join(text_blocks).strip()
        if not text:
            raise ProviderResponseError("Anthropic returned an empty response.")

        logger.debug("Anthropic generation completed in %.3fs", elapsed)
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_seconds=elapsed,
            raw=response,
        )
