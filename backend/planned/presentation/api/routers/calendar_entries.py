from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.repositories import CalendarEntryRepositoryProtocol
from planned.domain.entities import CalendarEntry
from planned.domain.value_objects.query import DateQuery
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.repositories import get_calendar_entry_repo

router = APIRouter()


@router.get("/today")
async def today(
    calendar_entry_repo: Annotated[CalendarEntryRepositoryProtocol, Depends(get_calendar_entry_repo)],
) -> list[CalendarEntry]:
    return await calendar_entry_repo.search_query(DateQuery(date=get_current_date()))

