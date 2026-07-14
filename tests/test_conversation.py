"""Tests for termi.core.conversation.ConversationManager."""

from __future__ import annotations

from termi.core.conversation import ConversationManager


def test_new_conversation_has_generated_id() -> None:
    manager = ConversationManager()
    assert manager.conversation_id
    assert len(manager) == 0


def test_add_turn_increases_length() -> None:
    manager = ConversationManager(history_size=5)
    manager.add_turn("create folder demo", "mkdir demo")
    assert len(manager) == 1


def test_history_size_limit_is_enforced() -> None:
    manager = ConversationManager(history_size=2)
    manager.add_turn("one", "cmd1")
    manager.add_turn("two", "cmd2")
    manager.add_turn("three", "cmd3")
    assert len(manager) == 2
    prompts = [turn.user_prompt for turn in manager.turns]
    assert prompts == ["two", "three"]


def test_build_messages_includes_system_and_history() -> None:
    manager = ConversationManager(history_size=5)
    manager.add_turn("create folder demo", "mkdir demo")
    messages = manager.build_messages("SYSTEM_PROMPT", "go inside it")

    assert messages[0].role == "system"
    assert messages[0].content == "SYSTEM_PROMPT"
    assert messages[1].role == "user"
    assert messages[1].content == "create folder demo"
    assert messages[2].role == "assistant"
    assert messages[2].content == "mkdir demo"
    assert messages[-1].role == "user"
    assert messages[-1].content == "go inside it"


def test_reset_clears_turns_and_changes_id() -> None:
    manager = ConversationManager()
    manager.add_turn("a", "b")
    old_id = manager.conversation_id
    manager.reset()
    assert len(manager) == 0
    assert manager.conversation_id != old_id


def test_set_history_size_trims_existing_turns() -> None:
    manager = ConversationManager(history_size=5)
    for i in range(5):
        manager.add_turn(f"prompt{i}", f"cmd{i}")
    manager.set_history_size(2)
    assert len(manager) == 2
