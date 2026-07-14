from __future__ import annotations

from termi.providers.base import BaseProvider, GenerationResult, Message
from termi.providers.factory import SUPPORTED_PROVIDERS, ProviderFactory
from termi.utils.logger import get_logger

logger = get_logger(__name__)


class ProviderManager:
    
    def __init__(self, provider_name: str, model: str | None = None) -> None:
        
        self._provider_name = provider_name
        self._provider: BaseProvider = ProviderFactory.create(provider_name, model)

    @property
    def active_provider(self) -> BaseProvider:
        return self._provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    def set_provider(self, provider_name: str, model: str | None = None) -> None:
        self._provider = ProviderFactory.create(provider_name, model)
        logger.info(
            "Active provider switched to '%s' (model=%s)", provider_name, self._provider.model
        )

    @staticmethod
    def list_providers() -> tuple[str, ...]:
        return SUPPORTED_PROVIDERS

    def generate(self, messages: list[Message]) -> GenerationResult:
        logger.debug(
            "Dispatching generation request to provider=%s model=%s",
            self._provider.name,
            self._provider.model,
        )
        return self._provider.generate(messages)
