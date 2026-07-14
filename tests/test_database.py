"""Tests for termi.database.database.Database."""

from __future__ import annotations

import pytest

from termi.database.database import Database
from termi.utils.exceptions import DatabaseError


@pytest.fixture
def db() -> Database:
    database = Database(db_path=":memory:")
    yield database
    database.close()


def test_schema_creates_history_table(db: Database) -> None:
    rows = db.query("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
    assert len(rows) == 1


def test_schema_creates_benchmark_table(db: Database) -> None:
    rows = db.query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='benchmark_results'"
    )
    assert len(rows) == 1


def test_execute_inserts_row(db: Database) -> None:
    cursor = db.execute(
        "INSERT INTO history (conversation_id, prompt, command, provider, model) "
        "VALUES (?, ?, ?, ?, ?)",
        ("conv-1", "list files", "ls -la", "groq", "llama-3.3-70b-versatile"),
    )
    assert cursor.lastrowid == 1


def test_query_returns_inserted_row(db: Database) -> None:
    db.execute(
        "INSERT INTO history (conversation_id, prompt, command, provider, model) "
        "VALUES (?, ?, ?, ?, ?)",
        ("conv-1", "list files", "ls -la", "groq", "llama-3.3-70b-versatile"),
    )
    rows = db.query("SELECT * FROM history WHERE conversation_id = ?", ("conv-1",))
    assert len(rows) == 1
    assert rows[0]["prompt"] == "list files"


def test_invalid_query_raises_database_error(db: Database) -> None:
    with pytest.raises(DatabaseError):
        db.execute("INSERT INTO not_a_table (x) VALUES (1)")


def test_context_manager_closes_connection() -> None:
    with Database(db_path=":memory:") as database:
        database.execute(
            "INSERT INTO history (conversation_id, prompt, command, provider, model) "
            "VALUES (?, ?, ?, ?, ?)",
            ("conv-1", "p", "c", "groq", "m"),
        )
    with pytest.raises(DatabaseError):
        database.query("SELECT 1")
