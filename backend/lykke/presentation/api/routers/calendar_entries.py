"""Router for Calendar Entry operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar_entry import (
    CreateCalendarEntryCommand,
    CreateCalendarEntryHandler,
    DeleteCalendarEntryCommand,
    DeleteCalendarEntryHandler,
    UpdateCalendarEntryCommand,
    UpdateCalendarEntryHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    CalendarEntryCreateSchema,
    CalendarEntrySchema,
    CalendarEntryUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_entry_to_schema
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory
from .dependencies.user import get_current_user

router = APIRouter()


@router.post("/", response_model=CalendarEntrySchema, status_code=201)
async def create_calendar_entry(
    data: CalendarEntryCreateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CalendarEntrySchema:
    """Create a first-party (Lykke) calendar entry. Timed events only."""
    create_handler = command_factory.create(CreateCalendarEntryHandler)
    entry = await create_handler.handle(
        CreateCalendarEntryCommand(
            name=data.name,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            category=data.category,
        )
    )
    return map_calendar_entry_to_schema(
        entry, user_timezone=user.settings.timezone
    )


@router.delete("/{uuid}", status_code=204)
async def delete_calendar_entry(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a calendar entry (user-scoped)."""
    delete_handler = command_factory.create(DeleteCalendarEntryHandler)
    await delete_handler.handle(DeleteCalendarEntryCommand(calendar_entry_id=uuid))


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
