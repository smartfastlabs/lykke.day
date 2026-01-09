"""Router for Calendar Entry Series operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
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


@router.get(
    "/",
    response_model=value_objects.PagedQueryResponse[CalendarEntrySeriesSchema],
)
async def list_calendar_entry_series(
    list_handler: Annotated[
        SearchCalendarEntrySeriesHandler, Depends(get_list_calendar_entry_series_handler)
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    calendar_id: UUID | None = Query(default=None),
) -> value_objects.PagedQueryResponse[CalendarEntrySeriesSchema]:
    """List calendar entry series with optional calendar filtering."""
    search_query = value_objects.CalendarEntrySeriesQuery(
        limit=limit,
        offset=offset,
        calendar_id=calendar_id,
    )
    result = await list_handler.run(search_query=search_query)
    items = [map_calendar_entry_series_to_schema(series) for series in result.items]
    return value_objects.PagedQueryResponse(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.post("/search", response_model=list[CalendarEntrySeriesSchema])
async def search_calendar_entry_series(
    list_handler: Annotated[
        SearchCalendarEntrySeriesHandler, Depends(get_list_calendar_entry_series_handler)
    ],
    query: value_objects.CalendarEntrySeriesQuery,
) -> list[CalendarEntrySeriesSchema]:
    """Search calendar entry series."""
    result = await list_handler.run(search_query=query)
    return [map_calendar_entry_series_to_schema(series) for series in result.items]


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


