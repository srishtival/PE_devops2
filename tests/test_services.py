import pytest

from src.database.connection import Database
from src.services.task_service import (
    TaskNotFoundError,
    TaskService,
    TaskValidationError,
)


@pytest.fixture
def service(tmp_path):
    database = Database(tmp_path / "services.db")
    database.initialize()
    return TaskService(database)


def test_create_and_retrieve_tasks(service):
    created = service.create_task("Write tests", "Cover service behavior")

    assert created.id > 0
    assert created.title == "Write tests"
    assert created.description == "Cover service behavior"
    assert created.completed is False
    assert service.get_task(created.id) == created
    assert service.get_tasks() == [created]


def test_update_existing_task(service):
    created = service.create_task("Old title")

    updated = service.update_task(
        created.id,
        {"title": "New title", "description": "Updated", "completed": True},
    )

    assert updated.title == "New title"
    assert updated.description == "Updated"
    assert updated.completed is True
    assert updated.created_at == created.created_at


def test_delete_task(service):
    created = service.create_task("Remove me")

    service.delete_task(created.id)

    assert service.get_tasks() == []
    with pytest.raises(TaskNotFoundError):
        service.get_task(created.id)


def test_complete_task(service):
    created = service.create_task("Finish me")

    completed = service.complete_task(created.id)

    assert completed.completed is True


@pytest.mark.parametrize("title", ["", "   ", None, 42, "x" * 201])
def test_rejects_invalid_titles(service, title):
    with pytest.raises(TaskValidationError):
        service.create_task(title)


def test_rejects_invalid_updates(service):
    task = service.create_task("Valid task")

    with pytest.raises(TaskValidationError):
        service.update_task(task.id, {"title": " "})
    with pytest.raises(TaskValidationError):
        service.update_task(task.id, {})


@pytest.mark.parametrize("operation", ["get", "update", "delete", "complete"])
def test_missing_task_id_raises_not_found(service, operation):
    with pytest.raises(TaskNotFoundError):
        if operation == "get":
            service.get_task(999)
        elif operation == "update":
            service.update_task(999, {"title": "Missing"})
        elif operation == "delete":
            service.delete_task(999)
        else:
            service.complete_task(999)