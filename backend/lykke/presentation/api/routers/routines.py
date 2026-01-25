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
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory

router = APIRouter()


@router.post("/{uuid}/actions", response_model=list[TaskSchema])
async def record_routine_action(
    uuid: UUID,
    action: value_objects.Action,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> list[TaskSchema]:
    """Record an action on all tasks in a routine for today."""
    handler = command_factory.create(RecordRoutineActionHandler)
    updated_tasks = await handler.handle(
        RecordRoutineActionCommand(routine_id=uuid, action=action)
    )
    return [map_task_to_schema(task) for task in updated_tasks]
