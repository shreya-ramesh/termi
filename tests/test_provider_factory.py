"""Tests for termi.providers.factory.ProviderFactory."""

from __future__ import annotations

import pytest

from termi.providers.anthropic_provider import AnthropicProvider
from termi.providers.factory import DEFAULT_MODELS, SUPPORTED_PROVIDERS, ProviderFactory
from termi.providers.gemini_provider import GeminiProvider
from termi.providers.groq_provider import GroqProvider
from termi.providers.ollama_provider import OllamaProvider
from termi.providers.openai_provider import OpenAIProvider
from termi.utils.exceptions import ProviderNotFoundError


def test_supported_providers_contains_all_five() -> None:
    assert set(SUPPORTED_PROVIDERS) == {"groq", "openai", "gemini", "anthropic", "ollama"}


@pytest.mark.parametrize(
    ("name", "expected_class"),
    [
        ("groq", GroqProvider),
        ("openai", OpenAIProvider),
        ("gemini", GeminiProvider),
        ("anthropic", AnthropicProvider),
        ("ollama", OllamaProvider),
    ],
)
def test_create_returns_correct_provider_class(name, expected_class, monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    provider = ProviderFactory.create(name)
    assert isinstance(provider, expected_class)
    assert provider.model == DEFAULT_MODELS[name]


def test_create_is_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    provider = ProviderFactory.create("GROQ")
    assert provider.name == "groq"


def test_create_uses_model_override(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    provider = ProviderFactory.create("groq", model="custom-model")
    assert provider.model == "custom-model"


def test_create_unknown_provider_raises() -> None:
    with pytest.raises(ProviderNotFoundError):
        ProviderFactory.create("not-a-real-provider")


def test_create_reads_api_key_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    provider = ProviderFactory.create("openai")
    assert provider.api_key == "sk-test-123"


def test_ollama_does_not_require_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    provider = ProviderFactory.create("ollama")
    assert provider.is_available() is True
    assert provider.api_key is None
