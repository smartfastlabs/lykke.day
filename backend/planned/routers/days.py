from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter

from planned.objects import Day
from planned.repositories import event_repo, task_repo
from planned.services import day_svc
from planned.utils.dates import get_current_date

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today() -> Day:
    return await day_svc.schedule_day(
        get_current_date(),
    )


@router.get("/today")
async def get_today() -> Day:
    return await day_svc.load_day(get_current_date())
