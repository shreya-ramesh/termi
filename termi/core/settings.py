from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from termi.utils.exceptions import ConfigurationError
from termi.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_SETTINGS_PATH = Path.home() / ".termi" / "settings.json"


@dataclass
class Settings:
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    safe_mode: bool = True
    auto_execute: bool = False
    history_size: int = 10
    theme: str = "default"
    shell_override: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        known_fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


class SettingsManager:

    def __init__(self, settings_path: Path | str | None = None) -> None:
        self.settings_path = Path(settings_path) if settings_path else DEFAULT_SETTINGS_PATH
        self._settings = self._load()

    @property
    def settings(self) -> Settings:
        return self._settings

    def _load(self) -> Settings:
        if not self.settings_path.exists():
            logger.info("No settings file found; creating defaults at %s", self.settings_path)
            settings = Settings()
            self._write(settings)
            return settings

        try:
            raw = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ConfigurationError(
                f"Failed to read settings file at {self.settings_path}: {exc}"
            ) from exc

        return Settings.from_dict(raw)

    def _write(self, settings: Settings) -> None:
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(
                json.dumps(settings.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise ConfigurationError(
                f"Failed to write settings file at {self.settings_path}: {exc}"
            ) from exc

    def save(self) -> None:
        self._write(self._settings)
        logger.debug("Settings saved to %s", self.settings_path)

    def update(self, **kwargs: object) -> Settings:
        known_fields = set(Settings.__dataclass_fields__)
        unknown = set(kwargs) - known_fields
        if unknown:
            raise ConfigurationError(f"Unknown setting(s): {', '.join(sorted(unknown))}")

        for key, value in kwargs.items():
            setattr(self._settings, key, value)

        self.save()
        return self._settings

    def reset(self) -> Settings:
        self._settings = Settings()
        self.save()
        return self._settings
