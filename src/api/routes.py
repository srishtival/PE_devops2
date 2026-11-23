"""REST endpoints for task management."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from src.database.models import Task
from src.services.task_service import (
    TaskNotFoundError,
    TaskService,
    TaskValidationError,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""

    model_config = ConfigDict(str_strip_whitespace=False)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    completed: StrictBool | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    created_at: str


def get_task_service(request: Request) -> TaskService:
    return request.app.state.task_service


TaskServiceDependency = Annotated[TaskService, Depends(get_task_service)]


def _response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        created_at=task.created_at.isoformat(),
    )


def _raise_http_error(error: Exception) -> NoReturn:
    if isinstance(error, TaskNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, TaskValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        )
    raise error


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, service: TaskServiceDependency) -> TaskResponse:
    try:
        return _response(service.create_task(payload.title, payload.description))
    except (TaskNotFoundError, TaskValidationError) as error:
        _raise_http_error(error)


@router.get("", response_model=list[TaskResponse])
def get_tasks(service: TaskServiceDependency) -> list[TaskResponse]:
    return [_response(task) for task in service.get_tasks()]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, service: TaskServiceDependency) -> TaskResponse:
    try:
        return _response(service.get_task(task_id))
    except TaskNotFoundError as error:
        _raise_http_error(error)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int, payload: TaskUpdate, service: TaskServiceDependency
) -> TaskResponse:
    try:
        values = payload.model_dump(exclude_unset=True)
        return _response(service.update_task(task_id, values))
    except (TaskNotFoundError, TaskValidationError) as error:
        _raise_http_error(error)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, service: TaskServiceDependency) -> TaskResponse:
    try:
        return _response(service.complete_task(task_id))
    except TaskNotFoundError as error:
        _raise_http_error(error)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, service: TaskServiceDependency) -> Response:
    try:
        service.delete_task(task_id)
    except TaskNotFoundError as error:
        _raise_http_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)