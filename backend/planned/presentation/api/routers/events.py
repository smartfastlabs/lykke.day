from fastapi import APIRouter, Depends

from planned.domain.entities import Event
from planned.infrastructure.repositories import EventRepository
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.repositories import get_event_repo

router = APIRouter()


@router.get("/today")
async def today(
    event_repo: EventRepository = Depends(get_event_repo),
) -> list[Event]:
    from planned.infrastructure.repositories.base import DateQuery

    return await event_repo.search_query(DateQuery(date=get_current_date()))
