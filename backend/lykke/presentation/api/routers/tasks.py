"""Routes for task operations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from lykke.application.commands import RecordTaskActionHandler
from lykke.domain import value_objects
from lykke.presentation.api.schemas import TaskSchema
from lykke.presentation.api.schemas.mappers import map_task_to_schema

from .dependencies.services import get_record_task_action_handler

router = APIRouter()


@router.post("/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    _id: uuid.UUID,
    action: value_objects.Action,
    handler: Annotated[
        RecordTaskActionHandler, Depends(get_record_task_action_handler)
    ],
) -> TaskSchema:
    """Record an action on a task."""
    task = await handler.record_task_action(
        task_id=_id,
        action=action,
    )
    return map_task_to_schema(task)
