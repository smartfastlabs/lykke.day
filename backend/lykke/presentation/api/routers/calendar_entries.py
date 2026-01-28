"""Router for Calendar Entry operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar_entry import (
    UpdateCalendarEntryCommand,
    UpdateCalendarEntryHandler,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import (
    CalendarEntrySchema,
    CalendarEntryUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_entry_to_schema
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory

router = APIRouter()


@router.put("/{uuid}", response_model=CalendarEntrySchema)
async def update_calendar_entry(
    uuid: UUID,
    update_data: CalendarEntryUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarEntrySchema:
    """Update a calendar entry."""
    update_handler = command_factory.create(UpdateCalendarEntryHandler)
    update_object = value_objects.CalendarEntryUpdateObject(
        name=update_data.name,
        status=update_data.status,
        attendance_status=update_data.attendance_status,
        starts_at=update_data.starts_at,
        ends_at=update_data.ends_at,
        frequency=update_data.frequency,
        category=update_data.category,
        calendar_entry_series_id=update_data.calendar_entry_series_id,
    )
    updated = await update_handler.handle(
        UpdateCalendarEntryCommand(calendar_entry_id=uuid, update_data=update_object)
    )
    return map_calendar_entry_to_schema(updated)
