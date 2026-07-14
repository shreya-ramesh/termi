from __future__ import annotations

from dataclasses import dataclass

from termi.database.database import Database
from termi.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class HistoryEntry:

    id: int
    conversation_id: str
    prompt: str
    command: str | None
    provider: str
    model: str
    execution_status: str
    exit_code: int | None
    output: str | None
    error: str | None
    created_at: str


class HistoryRepository:

    def __init__(self, database: Database) -> None:
        self._db = database

    def add_entry(
        self,
        conversation_id: str,
        prompt: str,
        command: str | None,
        provider: str,
        model: str,
        execution_status: str = "pending",
        exit_code: int | None = None,
        output: str | None = None,
        error: str | None = None,
    ) -> int:
        cursor = self._db.execute(
            """
            INSERT INTO history (
                conversation_id, prompt, command, provider, model,
                execution_status, exit_code, output, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                prompt,
                command,
                provider,
                model,
                execution_status,
                exit_code,
                output,
                error,
            ),
        )
        row_id = cursor.lastrowid
        logger.debug("Inserted history entry id=%s", row_id)
        return row_id

    def update_execution_result(
        self,
        entry_id: int,
        execution_status: str,
        exit_code: int | None,
        output: str | None,
        error: str | None,
    ) -> None:
        self._db.execute(
            """
            UPDATE history
            SET execution_status = ?, exit_code = ?, output = ?, error = ?
            WHERE id = ?
            """,
            (execution_status, exit_code, output, error, entry_id),
        )

    def get_recent(self, limit: int = 20) -> list[HistoryEntry]:
        """Return the most recent history entries, newest first."""
        rows = self._db.query(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_entry(row) for row in rows]

    def get_by_conversation(self, conversation_id: str) -> list[HistoryEntry]:
        rows = self._db.query(
            "SELECT * FROM history WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        )
        return [self._row_to_entry(row) for row in rows]

    def get_last_entry(self) -> HistoryEntry | None:
        rows = self._db.query("SELECT * FROM history ORDER BY id DESC LIMIT 1")
        return self._row_to_entry(rows[0]) if rows else None

    def clear(self) -> int:
        rows_before = self._db.query("SELECT COUNT(*) AS c FROM history")
        count = rows_before[0]["c"] if rows_before else 0
        self._db.execute("DELETE FROM history")
        logger.info("Cleared %d history entries", count)
        return count

    @staticmethod
    def _row_to_entry(row) -> HistoryEntry:  
        return HistoryEntry(
            id=row["id"],
            conversation_id=row["conversation_id"],
            prompt=row["prompt"],
            command=row["command"],
            provider=row["provider"],
            model=row["model"],
            execution_status=row["execution_status"],
            exit_code=row["exit_code"],
            output=row["output"],
            error=row["error"],
            created_at=row["created_at"],
        )
