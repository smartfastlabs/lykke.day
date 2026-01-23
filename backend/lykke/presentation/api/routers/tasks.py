"""Routes for task operations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from lykke.application.commands import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import AdhocTaskCreateSchema, TaskSchema
from lykke.presentation.api.schemas.mappers import map_task_to_schema
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory

router = APIRouter()


@router.post("/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    _id: uuid.UUID,
    action: value_objects.Action,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> TaskSchema:
    """Record an action on a task."""
    handler = command_factory.create(RecordTaskActionHandler)
    task = await handler.handle(RecordTaskActionCommand(task_id=_id, action=action))
    return map_task_to_schema(task)


@router.post("/adhoc", response_model=TaskSchema, status_code=201)
async def create_adhoc_task(
    task_data: AdhocTaskCreateSchema,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> TaskSchema:
    """Create an adhoc task."""
    handler = command_factory.create(CreateAdhocTaskHandler)
    schedule = (
        value_objects.TaskSchedule(**task_data.schedule.model_dump())
        if task_data.schedule
        else None
    )
    task = await handler.handle(
        CreateAdhocTaskCommand(
            scheduled_date=task_data.scheduled_date,
            name=task_data.name,
            category=task_data.category,
            description=task_data.description,
            schedule=schedule,
            tags=task_data.tags,
        )
    )
    return map_task_to_schema(task)
