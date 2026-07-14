"""Tests for termi.core.settings.SettingsManager."""

from __future__ import annotations

import pytest

from termi.core.settings import Settings, SettingsManager
from termi.utils.exceptions import ConfigurationError


def test_creates_default_settings_file_when_missing(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    manager = SettingsManager(settings_path=settings_path)

    assert settings_path.exists()
    assert manager.settings == Settings()


def test_loads_existing_settings_file(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        '{"provider": "openai", "model": "gpt-4o-mini", "safe_mode": false, '
        '"auto_execute": true, "history_size": 20, "theme": "dark", "shell_override": "zsh"}'
    )

    manager = SettingsManager(settings_path=settings_path)
    assert manager.settings.provider == "openai"
    assert manager.settings.safe_mode is False
    assert manager.settings.history_size == 20


def test_update_persists_changes(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    manager = SettingsManager(settings_path=settings_path)

    manager.update(provider="anthropic", history_size=15)

    reloaded = SettingsManager(settings_path=settings_path)
    assert reloaded.settings.provider == "anthropic"
    assert reloaded.settings.history_size == 15


def test_update_rejects_unknown_field(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    manager = SettingsManager(settings_path=settings_path)

    with pytest.raises(ConfigurationError):
        manager.update(not_a_real_field=True)


def test_reset_restores_defaults(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    manager = SettingsManager(settings_path=settings_path)
    manager.update(provider="openai")

    manager.reset()
    assert manager.settings == Settings()


def test_from_dict_ignores_unknown_keys() -> None:
    settings = Settings.from_dict({"provider": "gemini", "unknown_key": 123})
    assert settings.provider == "gemini"
    assert not hasattr(settings, "unknown_key")
