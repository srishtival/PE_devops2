import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as test_client:
        yield test_client


def test_create_and_retrieve_tasks(client):
    created = client.post(
        "/tasks", json={"title": "API task", "description": "Created over HTTP"}
    )

    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "API task"
    assert task["description"] == "Created over HTTP"
    assert task["completed"] is False
    assert client.get(f"/tasks/{task['id']}").json() == task
    assert client.get("/tasks").json() == [task]


def test_update_delete_and_complete_tasks(client):
    task = client.post("/tasks", json={"title": "Initial"}).json()

    updated = client.put(
        f"/tasks/{task['id']}", json={"title": "Updated", "description": "Details"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated"
    assert updated.json()["description"] == "Details"

    completed = client.post(f"/tasks/{task['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["completed"] is True

    deleted = client.delete(f"/tasks/{task['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


@pytest.mark.parametrize("title", ["", "  ", "x" * 201])
def test_invalid_titles_return_validation_errors(client, title):
    response = client.post("/tasks", json={"title": title})
    assert response.status_code == 422


def test_missing_tasks_and_invalid_updates_return_client_errors(client):
    assert client.get("/tasks/999").status_code == 404
    assert client.put("/tasks/999", json={"title": "Missing"}).status_code == 404
    assert client.delete("/tasks/999").status_code == 404
    assert client.post("/tasks/999/complete").status_code == 404
    assert client.put("/tasks/1", json={}).status_code == 422
    assert client.put("/tasks/1", json={"completed": "yes"}).status_code == 422