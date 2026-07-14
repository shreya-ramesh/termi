"""Google Gemini provider implementation.

This is the only module in the codebase permitted to import the
``google-genai`` SDK.
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

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider(BaseProvider):
    """LLM provider backed by Google's Gemini API."""

    name = "gemini"

    def generate(self, messages: list[Message]) -> GenerationResult:
        try:
            from google import genai
            from google.genai import types
            from google.genai.errors import ClientError
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderRequestError(
                "The 'google-genai' package is not installed. " "Run: pip install google-genai"
            ) from exc

        if not self.api_key:
            raise ProviderAuthenticationError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=self.api_key)

        system_parts = [m.content for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]

        contents = [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in conversation
        ]

        config = types.GenerateContentConfig(
            system_instruction="\n".join(system_parts) if system_parts else None,
            temperature=0.2,
        )

        start = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except ClientError as exc:
            status = getattr(exc, "code", None)
            if status in (401, 403):
                raise ProviderAuthenticationError(f"Gemini authentication failed: {exc}") from exc
            raise ProviderRequestError(f"Gemini request failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network/SDK errors vary
            raise ProviderRequestError(f"Gemini request failed: {exc}") from exc
        elapsed = time.perf_counter() - start

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise ProviderResponseError("Gemini returned an empty response.")

        logger.debug("Gemini generation completed in %.3fs", elapsed)
        return GenerationResult(
            text=text,
            provider=self.name,
            model=self.model,
            latency_seconds=elapsed,
            raw=response,
        )
