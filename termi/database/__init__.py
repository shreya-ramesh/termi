"""SQLite persistence layer: connection management and repositories."""

from termi.database.database import DEFAULT_DB_PATH, Database
from termi.database.history_repository import HistoryEntry, HistoryRepository

__all__ = ["Database", "DEFAULT_DB_PATH", "HistoryRepository", "HistoryEntry"]
