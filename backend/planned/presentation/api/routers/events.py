from typing import Annotated

from fastapi import APIRouter, Depends

from planned.application.repositories import EventRepositoryProtocol
from planned.domain.entities import Event
from planned.infrastructure.repositories.base.schema import DateQuery
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.repositories import get_event_repo

router = APIRouter()


@router.get("/today")
async def today(
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
) -> list[Event]:
    return await event_repo.search_query(DateQuery(date=get_current_date()))
