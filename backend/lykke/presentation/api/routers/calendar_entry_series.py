"""Router for Calendar Entry Series operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.commands.calendar_entry_series import (
    UpdateCalendarEntrySeriesCommand,
    UpdateCalendarEntrySeriesHandler,
)
from lykke.application.queries.calendar_entry_series import (
    GetCalendarEntrySeriesHandler,
    GetCalendarEntrySeriesQuery,
    SearchCalendarEntrySeriesHandler,
    SearchCalendarEntrySeriesQuery,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import (
    CalendarEntrySeriesSchema,
    CalendarEntrySeriesUpdateSchema,
    PagedResponseSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_calendar_entry_series_to_schema

from .dependencies.factories import get_command_handler, get_query_handler
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=CalendarEntrySeriesSchema)
async def get_calendar_entry_series(
    uuid: UUID,
    get_handler: Annotated[
        GetCalendarEntrySeriesHandler, Depends(get_query_handler(GetCalendarEntrySeriesHandler))
    ],
) -> CalendarEntrySeriesSchema:
    """Get a single calendar entry series by ID."""
    series = await get_handler.handle(GetCalendarEntrySeriesQuery(calendar_entry_series_id=uuid))
    return map_calendar_entry_series_to_schema(series)


@router.post(
    "/",
    response_model=PagedResponseSchema[CalendarEntrySeriesSchema],
)
async def search_calendar_entry_series(
    list_handler: Annotated[
        SearchCalendarEntrySeriesHandler,
        Depends(get_query_handler(SearchCalendarEntrySeriesHandler)),
    ],
    query: QuerySchema[value_objects.CalendarEntrySeriesQuery],
) -> PagedResponseSchema[CalendarEntrySeriesSchema]:
    """Search calendar entry series with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.CalendarEntrySeriesQuery)
    result = await list_handler.handle(SearchCalendarEntrySeriesQuery(search_query=search_query))
    return create_paged_response(result, map_calendar_entry_series_to_schema)


@router.put("/{uuid}", response_model=CalendarEntrySeriesSchema)
async def update_calendar_entry_series(
    uuid: UUID,
    update_data: CalendarEntrySeriesUpdateSchema,
    update_handler: Annotated[
        UpdateCalendarEntrySeriesHandler,
        Depends(get_command_handler(UpdateCalendarEntrySeriesHandler)),
    ],
) -> CalendarEntrySeriesSchema:
    """Update a calendar entry series."""
    update_object = value_objects.CalendarEntrySeriesUpdateObject(
        name=update_data.name,
        event_category=update_data.event_category,
    )
    updated = await update_handler.handle(UpdateCalendarEntrySeriesCommand(calendar_entry_series_id=uuid, update_data=update_object))
    return map_calendar_entry_series_to_schema(updated)
