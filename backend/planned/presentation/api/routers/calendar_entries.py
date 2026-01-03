from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.repositories import CalendarEntryRepositoryProtocol
from planned.core.utils.dates import get_current_date
from planned.domain import entities, value_objects
from planned.presentation.api.schemas.calendar_entry import CalendarEntrySchema
from planned.presentation.api.schemas.mappers import map_calendar_entry_to_schema

from .dependencies.repositories import get_calendar_entry_repo

router = APIRouter()


@router.get("/today", response_model=list[CalendarEntrySchema])
async def today(
    calendar_entry_repo: Annotated[CalendarEntryRepositoryProtocol, Depends(get_calendar_entry_repo)],
) -> list[CalendarEntrySchema]:
    entries = await calendar_entry_repo.search_query(value_objects.DateQuery(date=get_current_date()))
    return [map_calendar_entry_to_schema(entry) for entry in entries]

