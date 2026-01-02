"""Routes for task operations."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.commands import RecordTaskActionCommand
from planned.application.mediator import Mediator
from planned.application.repositories import TaskRepositoryProtocol
from planned.domain import entities, value_objects
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.repositories import get_task_repo
from .dependencies.services import get_mediator
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/today")
async def list_todays_tasks(
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> list[entities.Task]:
    """Get all tasks for today."""
    return await task_repo.search_query(
        value_objects.DateQuery(date=get_current_date())
    )


@router.post("/{date}/{_id}/actions")
async def add_task_action(
    date: dt.date,
    _id: uuid.UUID,
    action: entities.Action,
    user: Annotated[entities.User, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> entities.Task:
    _ = date  # Path parameter kept for API compatibility
    """Record an action on a task."""
    cmd = RecordTaskActionCommand(
        user_id=user.id,
        task_id=_id,
        action=action,
    )
    return await mediator.execute(cmd)
