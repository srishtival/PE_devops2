"""Business logic for creating and managing tasks."""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.database.connection import Database, DatabaseError
from src.database.models import Task

logger = logging.getLogger("task_management.services")


class TaskNotFoundError(LookupError):
    """Raised when a requested task does not exist."""


class TaskValidationError(ValueError):
    """Raised when task input does not meet application requirements."""


class TaskService:
    """Perform validated task operations against a SQLite database."""

    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _validate_title(title: Any) -> str:
        if not isinstance(title, str) or not title.strip():
            raise TaskValidationError("Task title must not be empty")
        if len(title.strip()) > 200:
            raise TaskValidationError("Task title must be at most 200 characters")
        return title.strip()

    @staticmethod
    def _validate_description(description: Any) -> str:
        if not isinstance(description, str):
            raise TaskValidationError("Task description must be a string")
        return description

    @staticmethod
    def _task(row: sqlite3.Row | None) -> Task:
        if row is None:
            raise TaskNotFoundError("Task not found")
        return Task.from_row(row)

    def create_task(self, title: str, description: str = "") -> Task:
        title = self._validate_title(title)
        description = self._validate_description(description)
        created_at = datetime.now(timezone.utc).isoformat()
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, description, created_at) VALUES (?, ?, ?)",
                (title, description, created_at),
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return self._task(row)

    def get_tasks(self) -> list[Task]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tasks ORDER BY id"
            ).fetchall()
        return [Task.from_row(row) for row in rows]

    def get_task(self, task_id: int) -> Task:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return self._task(row)

    def update_task(self, task_id: int, updates: dict[str, Any]) -> Task:
        allowed = {"title", "description", "completed"}
        if not updates or updates.keys() - allowed:
            raise TaskValidationError("Provide at least one valid task field to update")

        values: dict[str, Any] = {}
        if "title" in updates:
            values["title"] = self._validate_title(updates["title"])
        if "description" in updates:
            values["description"] = self._validate_description(updates["description"])
        if "completed" in updates:
            if not isinstance(updates["completed"], bool):
                raise TaskValidationError("Task completion status must be a boolean")
            values["completed"] = int(updates["completed"])

        assignments = ", ".join(f"{field} = ?" for field in values)
        parameters = [*values.values(), task_id]
        with self.database.connect() as connection:
            cursor = connection.execute(
                f"UPDATE tasks SET {assignments} WHERE id = ?", parameters
            )
            if cursor.rowcount == 0:
                raise TaskNotFoundError("Task not found")
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return self._task(row)

    def delete_task(self, task_id: int) -> None:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cursor.rowcount == 0:
                raise TaskNotFoundError("Task not found")

    def complete_task(self, task_id: int) -> Task:
        return self.update_task(task_id, {"completed": True})