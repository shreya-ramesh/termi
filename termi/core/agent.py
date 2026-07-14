from __future__ import annotations

import os
from dataclasses import dataclass

from termi.core.conversation import ConversationManager
from termi.core.error_explainer import ErrorExplainer
from termi.core.executor import CommandExecutor, ExecutionResult
from termi.core.explainer import CommandExplainer
from termi.core.intent import build_command_system_prompt, extract_command
from termi.core.provider_manager import ProviderManager
from termi.core.settings import SettingsManager
from termi.core.system import get_system_context
from termi.core.system_query import SystemInfoSnapshot, build_system_info_snapshot
from termi.database.database import Database
from termi.database.history_repository import HistoryRepository
from termi.utils.dangerous_commands import DangerAssessment, assess_command
from termi.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CommandProposal:

    history_id: int
    command: str
    danger: DangerAssessment
    provider: str
    model: str


class Agent:


    def __init__(
        self,
        settings_manager: SettingsManager,
        provider_manager: ProviderManager,
        database: Database,
        conversation_manager: ConversationManager | None = None,
    ) -> None:
        self.settings_manager = settings_manager
        self.provider_manager = provider_manager
        self.database = database
        self.history_repo = HistoryRepository(database)
        self.conversation = conversation_manager or ConversationManager(
            history_size=settings_manager.settings.history_size
        )
        self.explainer = CommandExplainer(provider_manager)
        self.error_explainer = ErrorExplainer(provider_manager)
        self._last_proposal: CommandProposal | None = None

    def _system_context_block(self) -> str:
        context = get_system_context(self.settings_manager.settings.shell_override)
        return context.as_prompt_context()

    def generate_command(self, prompt: str) -> CommandProposal:
        
        system_prompt = build_command_system_prompt(self._system_context_block())
        messages = self.conversation.build_messages(system_prompt, prompt)

        result = self.provider_manager.generate(messages)
        command = extract_command(result.text)

        self.conversation.add_turn(prompt, command)

        danger = assess_command(command)

        history_id = self.history_repo.add_entry(
            conversation_id=self.conversation.conversation_id,
            prompt=prompt,
            command=command,
            provider=result.provider,
            model=result.model,
            execution_status="pending",
        )

        proposal = CommandProposal(
            history_id=history_id,
            command=command,
            danger=danger,
            provider=result.provider,
            model=result.model,
        )
        self._last_proposal = proposal
        return proposal

    def execute_proposal(self, proposal: CommandProposal) -> ExecutionResult:
       
        executor = CommandExecutor(shell=self.settings_manager.settings.shell_override)
        result = executor.execute(proposal.command)

        status = "success" if result.succeeded else "failed"
        self.history_repo.update_execution_result(
            entry_id=proposal.history_id,
            execution_status=status,
            exit_code=result.exit_code,
            output=result.stdout,
            error=result.stderr,
        )
        return result

    def explain_command(self, command: str) -> str:
        return self.explainer.explain(command, self._system_context_block())

    def explain_failure(self, result: ExecutionResult) -> str:
        return self.error_explainer.explain_failure(result, self._system_context_block())

    def get_system_info_snapshot(self) -> SystemInfoSnapshot:
    
        context = get_system_context(self.settings_manager.settings.shell_override)
        executor = getattr(self, "_executor", None)
        cwd = executor.current_directory if executor is not None else os.getcwd()
        return build_system_info_snapshot(
            system_context=context,
            cwd=cwd,
            provider=self.provider_manager.provider_name,
            model=self.provider_manager.model,
        )

    def retry_last(self) -> CommandProposal | None:
       
        last_entry = self.history_repo.get_last_entry()
        if last_entry is None:
            return None
        return self.generate_command(last_entry.prompt)

    @property
    def last_proposal(self) -> CommandProposal | None:
        return self._last_proposal