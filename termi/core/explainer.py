from __future__ import annotations

from termi.core.provider_manager import ProviderManager
from termi.providers.base import Message
from termi.utils.logger import get_logger

logger = get_logger(__name__)


def build_explain_system_prompt(system_context: str) -> str:

    return (
        "You are Termi, an expert terminal assistant. Explain shell commands "
        "clearly and concisely for a developer audience.\n\n"
        f"{system_context}\n\n"
        "Rules:\n"
        "- Break down each meaningful flag/argument.\n"
        "- Mention any side effects or risks if relevant.\n"
        "- Keep the explanation focused and avoid unnecessary repetition.\n"
        "- Use plain text (no markdown headers)."
    )


class CommandExplainer:
    

    def __init__(self, provider_manager: ProviderManager) -> None:
        self._provider_manager = provider_manager

    def explain(self, command: str, system_context: str) -> str:
     
        messages = [
            Message(role="system", content=build_explain_system_prompt(system_context)),
            Message(role="user", content=f"Explain this command:\n\n{command}"),
        ]
        logger.debug("Requesting explanation for command: %s", command)
        result = self._provider_manager.generate(messages)
        return result.text
