import pytest

from src.database.connection import Database


def test_initialize_creates_tasks_table_and_is_idempotent(tmp_path):
    database = Database(tmp_path / "nested" / "tasks.db")

    database.initialize()
    database.initialize()

    with database.connect() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
    assert columns == {"id", "title", "description", "completed", "created_at"}


def test_database_persists_records_between_connections(tmp_path):
    database_path = tmp_path / "tasks.db"
    Database(database_path).initialize()

    with Database(database_path).connect() as connection:
        connection.execute(
            "INSERT INTO tasks (title, description, created_at) VALUES (?, ?, ?)",
            ("Persistent task", "Stored in SQLite", "2026-01-01T00:00:00+00:00"),
        )

    with Database(database_path).connect() as connection:
        row = connection.execute(
            "SELECT title, description FROM tasks WHERE id = 1"
        ).fetchone()

    assert row["title"] == "Persistent task"
    assert row["description"] == "Stored in SQLite"


def test_connection_rolls_back_failed_transaction(tmp_path):
    database = Database(tmp_path / "tasks.db")
    database.initialize()

    with pytest.raises(RuntimeError, match="abort transaction"):
        with database.connect() as connection:
            connection.execute(
                "INSERT INTO tasks (title, created_at) VALUES (?, ?)",
                ("Rolled back", "2026-01-01T00:00:00+00:00"),
            )
            raise RuntimeError("abort transaction")

    with database.connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    assert count == 0