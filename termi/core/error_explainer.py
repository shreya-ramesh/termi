"""Explains why a command failed and how to fix it, using the active LLM."""

from __future__ import annotations

from termi.core.executor import ExecutionResult
from termi.core.provider_manager import ProviderManager
from termi.providers.base import Message
from termi.utils.logger import get_logger

logger = get_logger(__name__)


def build_error_explainer_system_prompt(system_context: str) -> str:
    return (
        "You are Termi, an expert terminal assistant. A shell command just "
        "failed. Diagnose the failure for the user.\n\n"
        f"{system_context}\n\n"
        "Respond with exactly two labeled sections:\n"
        "Why it failed: <concise root-cause explanation>\n"
        "How to fix it: <concrete, actionable steps or a corrected command>\n"
        "Do not use markdown headers or code fences."
    )


class ErrorExplainer:

    def __init__(self, provider_manager: ProviderManager) -> None:
        self._provider_manager = provider_manager

    def explain_failure(self, result: ExecutionResult, system_context: str) -> str:
       
        user_prompt = (
            f"Command: {result.command}\n"
            f"Exit code: {result.exit_code}\n"
            f"Stderr:\n{result.stderr.strip() or '(empty)'}\n"
            f"Stdout:\n{result.stdout.strip() or '(empty)'}"
        )
        messages = [
            Message(
                role="system",
                content=build_error_explainer_system_prompt(system_context),
            ),
            Message(role="user", content=user_prompt),
        ]
        logger.debug("Requesting failure diagnosis for command: %s", result.command)
        response = self._provider_manager.generate(messages)
        return response.text
