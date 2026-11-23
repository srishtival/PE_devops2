# Task Management System

A Python task-management REST API built with FastAPI and SQLite. Task data is
stored in a local SQLite database, so it remains available across application
restarts.

## Features

- Create, list, retrieve, update, and delete tasks.
- Mark tasks complete through an explicit completion endpoint or task update.
- Validate task titles and return useful HTTP errors for invalid or missing tasks.
- Persist tasks in SQLite with UTC creation timestamps.
- Run isolated service, database, and API tests.

## Architecture

- **API (`src/api`)**: FastAPI routes and request/response validation.
- **Services (`src/services`)**: task validation and CRUD business logic.
- **Database (`src/database`)**: SQLite schema, connection lifecycle, and task model.
- **Application (`src/main.py`)**: configuration, logging, and app assembly.
- **Configuration (`config/settings.yaml`)**: database and application log paths.

## Directory structure

```text
.
├── config/
│   └── settings.yaml
├── docs/
│   └── architecture.md
├── logs/
│   └── failure.log
├── src/
│   ├── api/
│   │   └── routes.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── services/
│   │   └── task_service.py
│   └── main.py
├── tests/
│   ├── test_api.py
│   ├── test_database.py
│   └── test_services.py
├── requirements.txt
└── pytest.ini
```

## Installation

Python 3.12 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the application

From the repository root:

```bash
uvicorn src.main:app --reload
```

By default, the application creates `data/tasks.db` and appends application
errors to `logs/failure.log`. Update `config/settings.yaml` to change those
paths. The interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| `POST` | `/tasks` | Create a task with `title` and optional `description` | `201 Created` |
| `GET` | `/tasks` | List tasks in creation order | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve a task | `200 OK` |
| `PUT` | `/tasks/{id}` | Update one or more of `title`, `description`, `completed` | `200 OK` |
| `POST` | `/tasks/{id}/complete` | Mark a task complete | `200 OK` |
| `DELETE` | `/tasks/{id}` | Delete a task | `204 No Content` |

Invalid request values return `422 Unprocessable Entity`; a task that does not
exist returns `404 Not Found`.

## Run tests

```bash
python -m pytest
```

Tests use temporary SQLite databases and do not depend on application data.
GitHub Actions runs the suite on Python 3.12 and uploads `logs/failure.log`
when a workflow job fails.
