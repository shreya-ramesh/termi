"""Tests for termi.database.history_repository.HistoryRepository."""

from __future__ import annotations

import pytest

from termi.database.database import Database
from termi.database.history_repository import HistoryRepository


@pytest.fixture
def repo() -> HistoryRepository:
    database = Database(db_path=":memory:")
    yield HistoryRepository(database)
    database.close()


def test_add_entry_returns_id(repo: HistoryRepository) -> None:
    entry_id = repo.add_entry(
        conversation_id="conv-1",
        prompt="show files",
        command="ls",
        provider="groq",
        model="llama-3.3-70b-versatile",
    )
    assert entry_id == 1


def test_get_recent_returns_newest_first(repo: HistoryRepository) -> None:
    repo.add_entry("conv-1", "first", "cmd1", "groq", "model")
    repo.add_entry("conv-1", "second", "cmd2", "groq", "model")

    entries = repo.get_recent(limit=10)
    assert entries[0].prompt == "second"
    assert entries[1].prompt == "first"


def test_get_by_conversation_filters_correctly(repo: HistoryRepository) -> None:
    repo.add_entry("conv-1", "a", "cmd-a", "groq", "model")
    repo.add_entry("conv-2", "b", "cmd-b", "groq", "model")
    repo.add_entry("conv-1", "c", "cmd-c", "groq", "model")

    entries = repo.get_by_conversation("conv-1")
    assert [e.prompt for e in entries] == ["a", "c"]


def test_update_execution_result(repo: HistoryRepository) -> None:
    entry_id = repo.add_entry("conv-1", "prompt", "ls", "groq", "model")
    repo.update_execution_result(
        entry_id=entry_id,
        execution_status="success",
        exit_code=0,
        output="file1\nfile2",
        error=None,
    )
    entries = repo.get_by_conversation("conv-1")
    assert entries[0].execution_status == "success"
    assert entries[0].exit_code == 0
    assert entries[0].output == "file1\nfile2"


def test_get_last_entry_returns_none_when_empty(repo: HistoryRepository) -> None:
    assert repo.get_last_entry() is None


def test_get_last_entry_returns_most_recent(repo: HistoryRepository) -> None:
    repo.add_entry("conv-1", "first", "cmd1", "groq", "model")
    repo.add_entry("conv-1", "second", "cmd2", "groq", "model")

    last = repo.get_last_entry()
    assert last is not None
    assert last.prompt == "second"


def test_clear_removes_all_entries(repo: HistoryRepository) -> None:
    repo.add_entry("conv-1", "a", "cmd-a", "groq", "model")
    repo.add_entry("conv-1", "b", "cmd-b", "groq", "model")

    deleted_count = repo.clear()
    assert deleted_count == 2
    assert repo.get_recent() == []
