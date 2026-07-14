from __future__ import annotations

import os
from collections.abc import Callable

from termi.providers.anthropic_provider import DEFAULT_MODEL as ANTHROPIC_DEFAULT_MODEL
from termi.providers.anthropic_provider import AnthropicProvider
from termi.providers.base import BaseProvider
from termi.providers.gemini_provider import DEFAULT_MODEL as GEMINI_DEFAULT_MODEL
from termi.providers.gemini_provider import GeminiProvider
from termi.providers.groq_provider import DEFAULT_MODEL as GROQ_DEFAULT_MODEL
from termi.providers.groq_provider import GroqProvider
from termi.providers.ollama_provider import DEFAULT_BASE_URL as OLLAMA_DEFAULT_BASE_URL
from termi.providers.ollama_provider import DEFAULT_MODEL as OLLAMA_DEFAULT_MODEL
from termi.providers.ollama_provider import OllamaProvider
from termi.providers.openai_provider import DEFAULT_MODEL as OPENAI_DEFAULT_MODEL
from termi.providers.openai_provider import OpenAIProvider
from termi.utils.exceptions import ProviderNotFoundError

#: Environment variable name holding the API key for each provider.
_ENV_KEY_MAP: dict[str, str] = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": "",  # No key required.
}


DEFAULT_MODELS: dict[str, str] = {
    "groq": GROQ_DEFAULT_MODEL,
    "openai": OPENAI_DEFAULT_MODEL,
    "gemini": GEMINI_DEFAULT_MODEL,
    "anthropic": ANTHROPIC_DEFAULT_MODEL,
    "ollama": OLLAMA_DEFAULT_MODEL,
}

_ProviderConstructor = Callable[[str | None, str], BaseProvider]

_PROVIDER_CONSTRUCTORS: dict[str, _ProviderConstructor] = {
    "groq": lambda key, model: GroqProvider(api_key=key, model=model),
    "openai": lambda key, model: OpenAIProvider(api_key=key, model=model),
    "gemini": lambda key, model: GeminiProvider(api_key=key, model=model),
    "anthropic": lambda key, model: AnthropicProvider(api_key=key, model=model),
    "ollama": lambda key, model: OllamaProvider(
        api_key=key,
        model=model,
        base_url=os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL),
    ),
}

SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(_PROVIDER_CONSTRUCTORS.keys())


class ProviderFactory:

    @staticmethod
    def supported_providers() -> tuple[str, ...]:
        return SUPPORTED_PROVIDERS

    @staticmethod
    def create(provider_name: str, model: str | None = None) -> BaseProvider:
        key = provider_name.strip().lower()
        if key not in _PROVIDER_CONSTRUCTORS:
            raise ProviderNotFoundError(
                f"Unknown provider '{provider_name}'. "
                f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        env_var = _ENV_KEY_MAP[key]
        api_key = os.getenv(env_var) if env_var else None
        resolved_model = model or DEFAULT_MODELS[key]

        constructor = _PROVIDER_CONSTRUCTORS[key]
        return constructor(api_key, resolved_model)
