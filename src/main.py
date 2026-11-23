"""FastAPI application entry point."""

import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.database.connection import Database, DatabaseError
from src.services.task_service import TaskService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger("task_management")


def _settings() -> dict[str, Any]:
    settings_path = PROJECT_ROOT / "config" / "settings.yaml"
    with settings_path.open(encoding="utf-8") as settings_file:
        settings = yaml.safe_load(settings_file) or {}
    if not isinstance(settings, dict):
        raise ValueError(f"Expected a mapping in {settings_path}")
    return settings


def _database_path(configured_path: str | Path | None) -> Path:
    if configured_path is not None:
        return Path(configured_path)
    settings = _settings()
    database_config = settings.get("database", {})
    if not isinstance(database_config, dict):
        raise ValueError("The 'database' configuration must be a mapping")
    path = Path(database_config.get("path", "data/tasks.db"))
    return path if path.is_absolute() else PROJECT_ROOT / path


def _configure_logging() -> None:
    settings = _settings()
    logging_config = settings.get("logging", {})
    if not isinstance(logging_config, dict):
        raise ValueError("The 'logging' configuration must be a mapping")
    log_path = Path(logging_config.get("file", "logs/failure.log"))
    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == log_path.resolve()
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Create an application instance, optionally using an isolated database."""
    _configure_logging()
    database = Database(_database_path(database_path))
    database.initialize()

    app = FastAPI(
        title="Task Management System",
        description="A SQLite-backed REST API for managing tasks.",
        version="1.0.0",
    )
    app.state.task_service = TaskService(database)
    app.include_router(router)

    @app.exception_handler(DatabaseError)
    async def handle_database_error(
        request: Request, error: DatabaseError
    ) -> JSONResponse:
        logger.error(
            "Request %s %s failed due to a database error",
            request.method,
            request.url.path,
            exc_info=error,
        )
        return JSONResponse(
            status_code=500, content={"detail": "Task database operation failed"}
        )

    return app


app = create_app()