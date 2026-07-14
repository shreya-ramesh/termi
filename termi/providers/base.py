from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class GenerationResult:
    text: str
    provider: str
    model: str
    latency_seconds: float
    raw: object = field(default=None, repr=False, compare=False)


class BaseProvider(ABC):
    name: str = "base"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def generate(self, messages: list[Message]) -> GenerationResult:
        raise NotImplementedError

    def is_available(self) -> bool:
        return bool(self.api_key)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{self.__class__.__name__}(model={self.model!r})"
