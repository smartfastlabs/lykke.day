"""Router for Calendar CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar import (
    DeleteCalendarCommand,
    DeleteCalendarHandler,
    ResetCalendarDataCommand,
    ResetCalendarDataHandler,
    ResetCalendarSyncCommand,
    ResetCalendarSyncHandler,
    ResyncCalendarCommand,
    ResyncCalendarHandler,
    SubscribeCalendarCommand,
    SubscribeCalendarHandler,
    UnsubscribeCalendarCommand,
    UnsubscribeCalendarHandler,
    UpdateCalendarCommand,
    UpdateCalendarHandler,
)
from lykke.application.queries.calendar import (
    GetCalendarHandler,
    GetCalendarQuery,
    SearchCalendarsHandler,
    SearchCalendarsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.presentation.api.schemas import (
    CalendarSchema,
    CalendarUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_to_schema
from lykke.presentation.workers.tasks.calendar import sync_single_calendar_task

from .dependencies.factories import create_command_handler, create_query_handler
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarSchema)
async def get_calendar(
    uuid: UUID,
    handler: Annotated[GetCalendarHandler, Depends(create_query_handler(GetCalendarHandler))],
) -> CalendarSchema:
    """Get a single calendar by ID."""
    calendar = await handler.handle(GetCalendarQuery(calendar_id=uuid))
    return map_calendar_to_schema(calendar)


@router.post("/{uuid}/subscribe", response_model=CalendarSchema)
async def subscribe_calendar(
    uuid: UUID,
    query_handler: Annotated[GetCalendarHandler, Depends(create_query_handler(GetCalendarHandler))],
    command_handler: Annotated[SubscribeCalendarHandler, Depends(create_command_handler(SubscribeCalendarHandler))],
) -> CalendarSchema:
    """Enable push notifications for a calendar."""
    calendar = await query_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await command_handler.handle(
        SubscribeCalendarCommand(calendar=calendar)
    )
    # Trigger initial sync via background task
    await sync_single_calendar_task.kiq(
        user_id=updated.user_id,
        calendar_id=updated.id,
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}/subscribe", response_model=CalendarSchema)
async def unsubscribe_calendar(
    uuid: UUID,
    query_handler: Annotated[GetCalendarHandler, Depends(create_query_handler(GetCalendarHandler))],
    command_handler: Annotated[UnsubscribeCalendarHandler, Depends(create_command_handler(UnsubscribeCalendarHandler))],
) -> CalendarSchema:
    """Disable push notifications for a calendar."""
    calendar = await query_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await command_handler.handle(
        UnsubscribeCalendarCommand(calendar=calendar)
    )
    return map_calendar_to_schema(updated)


@router.post("/{uuid}/resync", response_model=CalendarSchema)
async def resync_calendar(
    uuid: UUID,
    query_handler: Annotated[GetCalendarHandler, Depends(create_query_handler(GetCalendarHandler))],
    command_handler: Annotated[ResyncCalendarHandler, Depends(create_command_handler(ResyncCalendarHandler))],
) -> CalendarSchema:
    """Resubscribe and fully resync a calendar."""
    calendar = await query_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await command_handler.handle(
        ResyncCalendarCommand(calendar=calendar)
    )
    return map_calendar_to_schema(updated)


@router.post("/reset-subscriptions", response_model=list[CalendarSchema])
async def reset_calendar_subscriptions(
    handler: Annotated[ResetCalendarDataHandler, Depends(create_command_handler(ResetCalendarDataHandler))],
) -> list[CalendarSchema]:
    """Delete all calendar data and refresh subscriptions for the user."""
    updated_calendars = await handler.handle(
        ResetCalendarDataCommand()
    )

    for calendar in updated_calendars:
        await sync_single_calendar_task.kiq(
            user_id=calendar.user_id,
            calendar_id=calendar.id,
        )

    return [map_calendar_to_schema(calendar) for calendar in updated_calendars]


@router.post("/reset-sync", response_model=list[CalendarSchema])
async def reset_calendar_sync(
    handler: Annotated[ResetCalendarSyncHandler, Depends(create_command_handler(ResetCalendarSyncHandler))],
) -> list[CalendarSchema]:
    """Reset calendar sync: unsubscribe, delete future events, resubscribe, and sync.

    This operation:
    1. Unsubscribes all calendars that have syncing enabled
    2. Deletes all future calendar entries for those calendars
    3. Resubscribes to updates for all calendars that were previously subscribed
    4. Performs initial sync for each calendar
    """
    updated_calendars = await handler.handle(
        ResetCalendarSyncCommand()
    )
    return [map_calendar_to_schema(calendar) for calendar in updated_calendars]


@router.post("/", response_model=PagedResponseSchema[CalendarSchema])
async def search_calendars(
    handler: Annotated[SearchCalendarsHandler, Depends(create_query_handler(SearchCalendarsHandler))],
    query: QuerySchema[value_objects.CalendarQuery],
) -> PagedResponseSchema[CalendarSchema]:
    """Search calendars with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.CalendarQuery)
    result = await handler.handle(
        SearchCalendarsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_calendar_to_schema)


@router.put("/{uuid}", response_model=CalendarSchema)
async def update_calendar(
    uuid: UUID,
    update_data: CalendarUpdateSchema,
    handler: Annotated[UpdateCalendarHandler, Depends(create_command_handler(UpdateCalendarHandler))],
) -> CalendarSchema:
    """Update a calendar."""
    # Convert schema to update object
    update_object = CalendarUpdateObject(
        name=update_data.name,
        auth_token_id=update_data.auth_token_id,
        default_event_category=update_data.default_event_category,
        last_sync_at=update_data.last_sync_at,
    )
    updated = await handler.handle(
        UpdateCalendarCommand(calendar_id=uuid, update_data=update_object)
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_calendar(
    uuid: UUID,
    handler: Annotated[DeleteCalendarHandler, Depends(create_command_handler(DeleteCalendarHandler))],
) -> None:
    """Delete a calendar."""
    await handler.handle(DeleteCalendarCommand(calendar_id=uuid))
