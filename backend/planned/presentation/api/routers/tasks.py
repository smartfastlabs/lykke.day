"""Routes for task operations."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import RecordTaskActionCommand
from planned.application.mediator import Mediator
from planned.application.repositories import TaskRepositoryProtocol
from planned.core.utils.dates import get_current_date
from planned.domain import entities, value_objects
from planned.presentation.api.schemas.mappers import map_task_to_schema
from planned.presentation.api.schemas.task import TaskSchema

from .dependencies.repositories import get_task_repo
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/today", response_model=list[TaskSchema])
async def list_todays_tasks(
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> list[TaskSchema]:
    """Get all tasks for today."""
    tasks = await task_repo.search_query(
        value_objects.DateQuery(date=get_current_date())
    )
    return [map_task_to_schema(task) for task in tasks]


@router.post("/{date}/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: entities.Action,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> TaskSchema:
    """Record an action on a task."""
    _ = date  # Path parameter kept for API compatibility
    cmd = RecordTaskActionCommand(
        user_id=user.id,
        task_id=_id,
        action=action,
    )
    task = await mediator.execute(cmd)
    return map_task_to_schema(task)
