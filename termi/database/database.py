from __future__ import annotations

import sqlite3
from pathlib import Path

from termi.utils.exceptions import DatabaseError
from termi.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_DB_PATH = Path.home() / ".termi" / "termi.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    command TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    execution_status TEXT NOT NULL DEFAULT 'pending',
    exit_code INTEGER,
    output TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_history_conversation_id
    ON history (conversation_id);

CREATE INDEX IF NOT EXISTS idx_history_created_at
    ON history (created_at);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    success INTEGER NOT NULL,
    latency_seconds REAL,
    error TEXT,
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

"""


class Database:

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = str(db_path) if db_path is not None else str(DEFAULT_DB_PATH)

        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to open database at {self.db_path}: {exc}") from exc

        self._initialize_schema()

    def _initialize_schema(self) -> None:
        try:
            with self._connection:
                self._connection.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to initialize schema: {exc}") from exc
        logger.debug("Database schema ready at %s", self.db_path)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            with self._connection:
                return self._connection.execute(query, params)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Query failed: {query!r} -- {exc}") from exc

    def query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        try:
            cursor = self._connection.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Query failed: {query!r} -- {exc}") from exc

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
