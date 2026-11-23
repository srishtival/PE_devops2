## Application layers

The application separates HTTP concerns, task rules, and persistence:

1. `src/api/routes.py` validates HTTP payloads with Pydantic and maps domain
   errors to HTTP status codes.
2. `src/services/task_service.py` validates task values and executes CRUD
   operations through parameterized SQLite queries.
3. `src/database/connection.py` creates the schema and owns each connection's
   commit, rollback, and close lifecycle.
4. `src/database/models.py` maps SQLite rows to immutable `Task` values.

`src/main.py` configures the app, database, and append-only error log.
`create_app(database_path=...)` allows tests to use a separate on-disk database
per test, while the default path is configured in `config/settings.yaml`.