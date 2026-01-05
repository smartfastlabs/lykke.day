from typing import Annotated

from fastapi import APIRouter, Depends
from planned.application.queries.calendar_entry import SearchCalendarEntriesHandler
from planned.core.utils.dates import get_current_date
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity
from planned.presentation.api.schemas import CalendarEntrySchema
from planned.presentation.api.schemas.mappers import map_calendar_entry_to_schema

from .dependencies.queries.calendar_entry import get_list_calendar_entries_handler

router = APIRouter()


@router.get("/today", response_model=list[CalendarEntrySchema])
async def today(
    list_calendar_entries_handler: Annotated[
        SearchCalendarEntriesHandler, Depends(get_list_calendar_entries_handler)
    ],
) -> list[CalendarEntrySchema]:
    result = await list_calendar_entries_handler.run(
        search_query=value_objects.CalendarEntryQuery(date=get_current_date()),
    )
    return [map_calendar_entry_to_schema(entry) for entry in result.items]
