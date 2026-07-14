from __future__ import annotations


class TermiError(Exception):
    """Base class for all Termi-specific exceptions."""


class ConfigurationError(TermiError):
    """Raised when settings or environment configuration is invalid."""


class ProviderError(TermiError):
    """Base class for all provider-related failures."""


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider name is not registered."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider rejects the supplied API key/credentials."""


class ProviderRequestError(ProviderError):
    """Raised when a provider request fails (network, API, timeout, etc.)."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns a malformed or empty response."""


class DatabaseError(TermiError):
    """Raised when a database operation fails."""


class ExecutionError(TermiError):
    """Raised when a shell command cannot be executed at all."""


class DangerousCommandError(TermiError):
    """Raised when a dangerous command is blocked in safe mode."""


class IntentError(TermiError):
    """Raised when the LLM output cannot be parsed into a command/intent."""
