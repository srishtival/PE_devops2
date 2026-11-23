"""Data models used by the task management application."""

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True, slots=True)
class Task:
    """A task as stored in the application database."""

    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Task":
        """Build a task from a SQLite row."""
        return cls(
            id=int(row["id"]),
            title=str(row["title"]),
            description=str(row["description"]),
            completed=bool(row["completed"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
