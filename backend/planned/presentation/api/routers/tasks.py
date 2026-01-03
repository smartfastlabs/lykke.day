"""Routes for task operations."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import RecordTaskActionCommand
from planned.application.mediator import Mediator
from planned.application.queries import ListEntitiesQuery
from planned.core.utils.dates import get_current_date
from planned.domain import value_objects
from planned.domain.entities import ActionEntity, TaskEntity, UserEntity
from planned.presentation.api.schemas import TaskSchema
from planned.presentation.api.schemas.mappers import map_task_to_schema

from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/today", response_model=list[TaskSchema])
async def list_todays_tasks(
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> list[TaskSchema]:
    """Get all tasks for today."""
    query = ListEntitiesQuery[TaskEntity](
        user_id=user.id,
        repository_name="tasks",
        search_query=value_objects.DateQuery(date=get_current_date()),
        paginate=False,
    )
    result = await mediator.query(query)
    tasks = result if isinstance(result, list) else result.items
    return [map_task_to_schema(task) for task in tasks]


@router.post("/{date}/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: ActionEntity,
    user: Annotated[UserEntity, Depends(get_current_user)],
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
