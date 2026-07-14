from __future__ import annotations

import uuid
from dataclasses import dataclass

from termi.providers.base import Message


@dataclass
class ConversationTurn:

    user_prompt: str
    assistant_reply: str


class ConversationManager:
   
    def __init__(self, history_size: int = 10, conversation_id: str | None = None) -> None:
        self.history_size = max(0, history_size)
        self.conversation_id: str = conversation_id or str(uuid.uuid4())
        self._turns: list[ConversationTurn] = []

    def add_turn(self, user_prompt: str, assistant_reply: str) -> None:
        self._turns.append(ConversationTurn(user_prompt, assistant_reply))
        if self.history_size and len(self._turns) > self.history_size:
            self._turns = self._turns[-self.history_size :]

    def set_history_size(self, size: int) -> None:
        self.history_size = max(0, size)
        if self.history_size and len(self._turns) > self.history_size:
            self._turns = self._turns[-self.history_size :]

    def build_messages(self, system_prompt: str, user_prompt: str) -> list[Message]:
        messages: list[Message] = [Message(role="system", content=system_prompt)]
        for turn in self._turns:
            messages.append(Message(role="user", content=turn.user_prompt))
            messages.append(Message(role="assistant", content=turn.assistant_reply))
        messages.append(Message(role="user", content=user_prompt))
        return messages

    def reset(self, new_conversation_id: str | None = None) -> None:
        self._turns.clear()
        self.conversation_id = new_conversation_id or str(uuid.uuid4())

    @property
    def turns(self) -> list[ConversationTurn]:
        return list(self._turns)

    def __len__(self) -> int:
        return len(self._turns)
