"""Router for routine actions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands import (
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import TaskSchema
from lykke.presentation.api.schemas.mappers import map_task_to_schema

from .dependencies.factories import create_command_handler

router = APIRouter()


@router.post("/{uuid}/actions", response_model=list[TaskSchema])
async def record_routine_action(
    uuid: UUID,
    action: value_objects.Action,
    handler: Annotated[
        RecordRoutineActionHandler,
        Depends(create_command_handler(RecordRoutineActionHandler)),
    ],
) -> list[TaskSchema]:
    """Record an action on all tasks in a routine for today."""
    updated_tasks = await handler.handle(
        RecordRoutineActionCommand(routine_id=uuid, action=action)
    )
    return [map_task_to_schema(task) for task in updated_tasks]
