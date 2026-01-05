"""Routes for task operations."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import RecordTaskActionHandler
from planned.application.queries.task import SearchTasksHandler
from planned.core.utils.dates import get_current_date
from planned.domain import value_objects
from planned.domain.entities import TaskEntity
from planned.presentation.api.schemas import TaskSchema
from planned.presentation.api.schemas.mappers import map_task_to_schema

from .dependencies.queries.task import get_list_tasks_handler
from .dependencies.services import get_record_task_action_handler

router = APIRouter()


@router.get("/today", response_model=list[TaskSchema])
async def list_todays_tasks(
    list_tasks_handler: Annotated[SearchTasksHandler, Depends(get_list_tasks_handler)],
) -> list[TaskSchema]:
    """Get all tasks for today."""
    result = await list_tasks_handler.run(
        search_query=value_objects.TaskQuery(date=get_current_date()),
    )
    return [map_task_to_schema(task) for task in result.items]


@router.post("/{date}/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: value_objects.Action,
    handler: Annotated[
        RecordTaskActionHandler, Depends(get_record_task_action_handler)
    ],
) -> TaskSchema:
    """Record an action on a task."""
    _ = date  # Path parameter kept for API compatibility
    task = await handler.record_task_action(
        task_id=_id,
        action=action,
    )
    return map_task_to_schema(task)
