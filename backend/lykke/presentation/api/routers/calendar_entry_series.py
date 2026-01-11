"""Router for Calendar Entry Series operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar_entry_series import (
    UpdateCalendarEntrySeriesHandler,
)
from lykke.application.queries.calendar_entry_series import (
    GetCalendarEntrySeriesHandler,
    SearchCalendarEntrySeriesHandler,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import (
    CalendarEntrySeriesSchema,
    CalendarEntrySeriesUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_entry_series_to_schema

from .dependencies.commands.calendar_entry_series import (
    get_update_calendar_entry_series_handler,
)
from .dependencies.queries.calendar_entry_series import (
    get_get_calendar_entry_series_handler,
    get_list_calendar_entry_series_handler,
)

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarEntrySeriesSchema)
async def get_calendar_entry_series(
    uuid: UUID,
    get_handler: Annotated[
        GetCalendarEntrySeriesHandler, Depends(get_get_calendar_entry_series_handler)
    ],
) -> CalendarEntrySeriesSchema:
    """Get a single calendar entry series by ID."""
    series = await get_handler.run(series_id=uuid)
    return map_calendar_entry_series_to_schema(series)


@router.post(
    "/",
    response_model=PagedResponseSchema[CalendarEntrySeriesSchema],
)
async def search_calendar_entry_series(
    list_handler: Annotated[
        SearchCalendarEntrySeriesHandler,
        Depends(get_list_calendar_entry_series_handler),
    ],
    query: QuerySchema[value_objects.CalendarEntrySeriesQuery],
) -> PagedResponseSchema[CalendarEntrySeriesSchema]:
    """Search calendar entry series with pagination and optional filters."""
    # Build the search query from the request
    filters = query.filters or value_objects.CalendarEntrySeriesQuery()
    search_query = value_objects.CalendarEntrySeriesQuery(
        limit=query.limit,
        offset=query.offset,
        calendar_id=filters.calendar_id,
        platform_id=filters.platform_id,
        created_before=filters.created_before,
        created_after=filters.created_after,
        order_by=filters.order_by,
        order_by_desc=filters.order_by_desc,
    )
    result = await list_handler.run(search_query=search_query)
    items = [map_calendar_entry_series_to_schema(series) for series in result.items]
    return PagedResponseSchema(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.put("/{uuid}", response_model=CalendarEntrySeriesSchema)
async def update_calendar_entry_series(
    uuid: UUID,
    update_data: CalendarEntrySeriesUpdateSchema,
    update_handler: Annotated[
        UpdateCalendarEntrySeriesHandler,
        Depends(get_update_calendar_entry_series_handler),
    ],
) -> CalendarEntrySeriesSchema:
    """Update a calendar entry series."""
    update_object = value_objects.CalendarEntrySeriesUpdateObject(
        name=update_data.name,
        event_category=update_data.event_category,
    )
    updated = await update_handler.run(series_id=uuid, update_data=update_object)
    return map_calendar_entry_series_to_schema(updated)
