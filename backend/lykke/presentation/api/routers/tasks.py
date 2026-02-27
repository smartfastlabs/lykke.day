"""Routes for task operations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from lykke.application.commands import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    DeleteTaskCommand,
    DeleteTaskHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
    RescheduleTaskCommand,
    RescheduleTaskHandler,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import AdhocTaskCreateSchema, TaskSchema
from lykke.presentation.api.schemas.mappers import map_task_to_schema
from lykke.presentation.api.schemas.task import TaskRescheduleSchema

from .dependencies.factories import create_command_handler

router = APIRouter()


@router.post("/{_id}/actions", response_model=TaskSchema)
async def add_task_action(
    _id: uuid.UUID,
    action: value_objects.Action,
    handler: Annotated[
        RecordTaskActionHandler, Depends(create_command_handler(RecordTaskActionHandler))
    ],
) -> TaskSchema:
    """Record an action on a task."""
    task = await handler.handle(RecordTaskActionCommand(task_id=_id, action=action))
    return map_task_to_schema(task)


@router.post("/{_id}/reschedule", response_model=TaskSchema)
async def reschedule_task(
    _id: uuid.UUID,
    payload: TaskRescheduleSchema,
    handler: Annotated[
        RescheduleTaskHandler, Depends(create_command_handler(RescheduleTaskHandler))
    ],
) -> TaskSchema:
    """Reschedule a task to a new date."""
    task = await handler.handle(
        RescheduleTaskCommand(task_id=_id, scheduled_date=payload.scheduled_date)
    )
    return map_task_to_schema(task)


@router.delete("/{_id}", status_code=204)
async def delete_task(
    _id: uuid.UUID,
    handler: Annotated[
        DeleteTaskHandler, Depends(create_command_handler(DeleteTaskHandler))
    ],
) -> None:
    """Delete a task."""
    await handler.handle(DeleteTaskCommand(task_id=_id))


@router.post("/adhoc", response_model=TaskSchema, status_code=201)
async def create_adhoc_task(
    task_data: AdhocTaskCreateSchema,
    handler: Annotated[
        CreateAdhocTaskHandler, Depends(create_command_handler(CreateAdhocTaskHandler))
    ],
) -> TaskSchema:
    """Create an adhoc or reminder task."""
    time_window = (
        value_objects.TimeWindow(**task_data.time_window.model_dump())
        if task_data.time_window
        else None
    )
    task_type = task_data.type
    task = await handler.handle(
        CreateAdhocTaskCommand(
            scheduled_date=task_data.scheduled_date,
            name=task_data.name,
            category=task_data.category,
            type=task_type,
            description=task_data.description,
            time_window=time_window,
            tags=task_data.tags,
        )
    )
    return map_task_to_schema(task)
