"""Tests for termi.core.provider_manager.ProviderManager."""

from __future__ import annotations

import pytest

from termi.core.provider_manager import ProviderManager
from termi.providers.base import GenerationResult, Message


@pytest.fixture(autouse=True)
def _fake_keys(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


def test_initial_provider_is_active(monkeypatch) -> None:
    manager = ProviderManager("groq")
    assert manager.provider_name == "groq"


def test_set_provider_switches_active_provider() -> None:
    manager = ProviderManager("groq")
    manager.set_provider("openai")
    assert manager.provider_name == "openai"


def test_list_providers_returns_all_supported() -> None:
    providers = ProviderManager.list_providers()
    assert "groq" in providers
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers
    assert "ollama" in providers


def test_generate_delegates_to_active_provider(monkeypatch) -> None:
    manager = ProviderManager("groq")

    def fake_generate(self, messages):
        return GenerationResult(
            text="ls -la", provider="groq", model=self.model, latency_seconds=0.01
        )

    monkeypatch.setattr(
        "termi.providers.groq_provider.GroqProvider.generate", fake_generate, raising=True
    )

    result = manager.generate([Message(role="user", content="list files")])
    assert result.text == "ls -la"
    assert result.provider == "groq"


def test_model_property_reflects_active_provider() -> None:
    manager = ProviderManager("groq", model="custom-model")
    assert manager.model == "custom-model"
