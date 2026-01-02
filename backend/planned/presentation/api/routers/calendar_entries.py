from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.repositories import CalendarEntryRepositoryProtocol
from planned.domain import entities, value_objects
from planned.core.utils.dates import get_current_date

from .dependencies.repositories import get_calendar_entry_repo

router = APIRouter()


@router.get("/today")
async def today(
    calendar_entry_repo: Annotated[CalendarEntryRepositoryProtocol, Depends(get_calendar_entry_repo)],
) -> list[entities.CalendarEntry]:
    return await calendar_entry_repo.search_query(value_objects.DateQuery(date=get_current_date()))

