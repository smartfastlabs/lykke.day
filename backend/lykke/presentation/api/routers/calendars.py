"""Router for Calendar CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar import (
    CreateCalendarCommand,
    CreateCalendarHandler,
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
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.presentation.api.schemas import (
    CalendarCreateSchema,
    CalendarSchema,
    CalendarUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)
from lykke.presentation.workers.tasks.calendar import sync_single_calendar_task

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarSchema)
async def get_calendar(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> CalendarSchema:
    """Get a single calendar by ID."""
    handler = query_factory.create(GetCalendarHandler)
    calendar = await handler.handle(GetCalendarQuery(calendar_id=uuid))
    return map_calendar_to_schema(calendar)


@router.post("/{uuid}/subscribe", response_model=CalendarSchema)
async def subscribe_calendar(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarSchema:
    """Enable push notifications for a calendar."""
    get_calendar_handler = query_factory.create(GetCalendarHandler)
    subscribe_calendar_handler = command_factory.create(SubscribeCalendarHandler)
    calendar = await get_calendar_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await subscribe_calendar_handler.handle(
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
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarSchema:
    """Disable push notifications for a calendar."""
    get_calendar_handler = query_factory.create(GetCalendarHandler)
    unsubscribe_calendar_handler = command_factory.create(UnsubscribeCalendarHandler)
    calendar = await get_calendar_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await unsubscribe_calendar_handler.handle(
        UnsubscribeCalendarCommand(calendar=calendar)
    )
    return map_calendar_to_schema(updated)


@router.post("/{uuid}/resync", response_model=CalendarSchema)
async def resync_calendar(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarSchema:
    """Resubscribe and fully resync a calendar."""
    get_calendar_handler = query_factory.create(GetCalendarHandler)
    resync_calendar_handler = command_factory.create(ResyncCalendarHandler)
    calendar = await get_calendar_handler.handle(GetCalendarQuery(calendar_id=uuid))
    updated = await resync_calendar_handler.handle(
        ResyncCalendarCommand(calendar=calendar)
    )
    return map_calendar_to_schema(updated)


@router.post("/reset-subscriptions", response_model=list[CalendarSchema])
async def reset_calendar_subscriptions(
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> list[CalendarSchema]:
    """Delete all calendar data and refresh subscriptions for the user."""
    reset_calendar_data_handler = command_factory.create(ResetCalendarDataHandler)
    updated_calendars = await reset_calendar_data_handler.handle(
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
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> list[CalendarSchema]:
    """Reset calendar sync: unsubscribe, delete future events, resubscribe, and sync.

    This operation:
    1. Unsubscribes all calendars that have syncing enabled
    2. Deletes all future calendar entries for those calendars
    3. Resubscribes to updates for all calendars that were previously subscribed
    4. Performs initial sync for each calendar
    """
    reset_calendar_sync_handler = command_factory.create(ResetCalendarSyncHandler)
    updated_calendars = await reset_calendar_sync_handler.handle(
        ResetCalendarSyncCommand()
    )
    return [map_calendar_to_schema(calendar) for calendar in updated_calendars]


@router.post("/", response_model=PagedResponseSchema[CalendarSchema])
async def search_calendars(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.CalendarQuery],
) -> PagedResponseSchema[CalendarSchema]:
    """Search calendars with pagination and optional filters."""
    list_calendars_handler = query_factory.create(SearchCalendarsHandler)
    search_query = build_search_query(query, value_objects.CalendarQuery)
    result = await list_calendars_handler.handle(
        SearchCalendarsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_calendar_to_schema)


@router.post("/create", response_model=CalendarSchema)
async def create_calendar(
    calendar_data: CalendarCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarSchema:
    """Create a new calendar."""
    create_calendar_handler = command_factory.create(CreateCalendarHandler)
    # Convert schema to entity (id is optional for create, entity will generate it if None)
    calendar = CalendarEntity(
        user_id=user.id,
        name=calendar_data.name,
        auth_token_id=calendar_data.auth_token_id,
        platform_id=calendar_data.platform_id,
        platform=calendar_data.platform,
        last_sync_at=calendar_data.last_sync_at,
        default_event_category=calendar_data.default_event_category,
    )
    created = await create_calendar_handler.handle(
        CreateCalendarCommand(calendar=calendar)
    )
    return map_calendar_to_schema(created)


@router.put("/{uuid}", response_model=CalendarSchema)
async def update_calendar(
    uuid: UUID,
    update_data: CalendarUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> CalendarSchema:
    """Update a calendar."""
    update_calendar_handler = command_factory.create(UpdateCalendarHandler)
    # Convert schema to update object
    update_object = CalendarUpdateObject(
        name=update_data.name,
        auth_token_id=update_data.auth_token_id,
        default_event_category=update_data.default_event_category,
        last_sync_at=update_data.last_sync_at,
    )
    updated = await update_calendar_handler.handle(
        UpdateCalendarCommand(calendar_id=uuid, update_data=update_object)
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_calendar(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a calendar."""
    delete_calendar_handler = command_factory.create(DeleteCalendarHandler)
    await delete_calendar_handler.handle(DeleteCalendarCommand(calendar_id=uuid))
