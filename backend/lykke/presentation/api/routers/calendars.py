"""Router for Calendar CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from lykke.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    ResyncCalendarHandler,
    ResetCalendarDataHandler,
    SubscribeCalendarHandler,
    UnsubscribeCalendarHandler,
    UpdateCalendarHandler,
)
from lykke.application.queries.calendar import (
    GetCalendarHandler,
    SearchCalendarsHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.presentation.api.schemas import (
    CalendarCreateSchema,
    CalendarSchema,
    CalendarUpdateSchema,
    PagedResponseSchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_to_schema
from lykke.presentation.workers.tasks import sync_single_calendar_task

from .dependencies.commands.calendar import (
    get_create_calendar_handler,
    get_delete_calendar_handler,
    get_resync_calendar_handler,
    get_reset_calendar_data_handler,
    get_subscribe_calendar_handler,
    get_unsubscribe_calendar_handler,
    get_update_calendar_handler,
)
from .dependencies.queries.calendar import (
    get_get_calendar_handler,
    get_list_calendars_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarSchema)
async def get_calendar(
    uuid: UUID,
    get_calendar_handler: Annotated[
        GetCalendarHandler, Depends(get_get_calendar_handler)
    ],
) -> CalendarSchema:
    """Get a single calendar by ID."""
    calendar = await get_calendar_handler.run(calendar_id=uuid)
    return map_calendar_to_schema(calendar)


@router.post("/{uuid}/subscribe", response_model=CalendarSchema)
async def subscribe_calendar(
    uuid: UUID,
    get_calendar_handler: Annotated[
        GetCalendarHandler, Depends(get_get_calendar_handler)
    ],
    subscribe_calendar_handler: Annotated[
        SubscribeCalendarHandler, Depends(get_subscribe_calendar_handler)
    ],
) -> CalendarSchema:
    """Enable push notifications for a calendar."""
    calendar = await get_calendar_handler.run(calendar_id=uuid)
    updated = await subscribe_calendar_handler.subscribe(calendar=calendar)
    # Trigger initial sync via background task
    await sync_single_calendar_task.kiq(
        user_id=updated.user_id,
        calendar_id=updated.id,
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}/subscribe", response_model=CalendarSchema)
async def unsubscribe_calendar(
    uuid: UUID,
    get_calendar_handler: Annotated[
        GetCalendarHandler, Depends(get_get_calendar_handler)
    ],
    unsubscribe_calendar_handler: Annotated[
        UnsubscribeCalendarHandler, Depends(get_unsubscribe_calendar_handler)
    ],
) -> CalendarSchema:
    """Disable push notifications for a calendar."""
    calendar = await get_calendar_handler.run(calendar_id=uuid)
    updated = await unsubscribe_calendar_handler.unsubscribe(calendar=calendar)
    return map_calendar_to_schema(updated)


@router.post("/{uuid}/resync", response_model=CalendarSchema)
async def resync_calendar(
    uuid: UUID,
    get_calendar_handler: Annotated[
        GetCalendarHandler, Depends(get_get_calendar_handler)
    ],
    resync_calendar_handler: Annotated[
        ResyncCalendarHandler, Depends(get_resync_calendar_handler)
    ],
) -> CalendarSchema:
    """Resubscribe and fully resync a calendar."""
    calendar = await get_calendar_handler.run(calendar_id=uuid)
    updated = await resync_calendar_handler.resync(calendar=calendar)
    return map_calendar_to_schema(updated)


@router.post("/reset-subscriptions", response_model=list[CalendarSchema])
async def reset_calendar_subscriptions(
    reset_calendar_data_handler: Annotated[
        ResetCalendarDataHandler, Depends(get_reset_calendar_data_handler)
    ],
) -> list[CalendarSchema]:
    """Delete all calendar data and refresh subscriptions for the user."""
    updated_calendars = await reset_calendar_data_handler.reset()

    for calendar in updated_calendars:
        await sync_single_calendar_task.kiq(
            user_id=calendar.user_id,
            calendar_id=calendar.id,
        )

    return [map_calendar_to_schema(calendar) for calendar in updated_calendars]


@router.get("/", response_model=PagedResponseSchema[CalendarSchema])
async def list_calendars(
    list_calendars_handler: Annotated[
        SearchCalendarsHandler, Depends(get_list_calendars_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PagedResponseSchema[CalendarSchema]:
    """List calendars with pagination."""
    result = await list_calendars_handler.run(
        search_query=value_objects.CalendarQuery(limit=limit, offset=offset),
    )
    paged_response = result
    # Convert entities to schemas
    calendar_schemas = [map_calendar_to_schema(c) for c in paged_response.items]
    return PagedResponseSchema(
        items=calendar_schemas,
        total=paged_response.total,
        limit=paged_response.limit,
        offset=paged_response.offset,
        has_next=paged_response.has_next,
        has_previous=paged_response.has_previous,
    )


@router.post("/", response_model=CalendarSchema)
async def create_calendar(
    calendar_data: CalendarCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_calendar_handler: Annotated[
        CreateCalendarHandler, Depends(get_create_calendar_handler)
    ],
) -> CalendarSchema:
    """Create a new calendar."""
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
    created = await create_calendar_handler.run(calendar=calendar)
    return map_calendar_to_schema(created)


@router.put("/{uuid}", response_model=CalendarSchema)
async def update_calendar(
    uuid: UUID,
    update_data: CalendarUpdateSchema,
    update_calendar_handler: Annotated[
        UpdateCalendarHandler, Depends(get_update_calendar_handler)
    ],
) -> CalendarSchema:
    """Update a calendar."""
    # Convert schema to update object
    from lykke.domain.value_objects import CalendarUpdateObject

    update_object = CalendarUpdateObject(
        name=update_data.name,
        auth_token_id=update_data.auth_token_id,
        default_event_category=update_data.default_event_category,
        last_sync_at=update_data.last_sync_at,
    )
    updated = await update_calendar_handler.run(
        calendar_id=uuid, update_data=update_object
    )
    return map_calendar_to_schema(updated)


@router.delete("/{uuid}", status_code=200)
async def delete_calendar(
    uuid: UUID,
    delete_calendar_handler: Annotated[
        DeleteCalendarHandler, Depends(get_delete_calendar_handler)
    ],
) -> None:
    """Delete a calendar."""
    await delete_calendar_handler.run(calendar_id=uuid)
