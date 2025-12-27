from fastapi import APIRouter, Depends

from planned.objects import Event
from planned.repositories import EventRepository
from planned.utils.dates import get_current_date

from .dependencies.repositories import get_event_repo

router = APIRouter()


@router.get("/today")
async def today(
    event_repo: EventRepository = Depends(get_event_repo),
) -> list[Event]:
    return await event_repo.search(get_current_date())
