"""LLM provider integrations.

Every provider implements :class:`~termi.providers.base.BaseProvider`.
Consumers outside this package should obtain provider instances via
:class:`~termi.providers.factory.ProviderFactory` and never import a
concrete provider or vendor SDK directly.
"""

from termi.providers.base import BaseProvider, GenerationResult, Message
from termi.providers.factory import DEFAULT_MODELS, SUPPORTED_PROVIDERS, ProviderFactory

__all__ = [
    "BaseProvider",
    "GenerationResult",
    "Message",
    "ProviderFactory",
    "SUPPORTED_PROVIDERS",
    "DEFAULT_MODELS",
]
