import datetime

from fastapi import APIRouter

from planned.objects import DayContext, Routine, Task
from planned.repositories import routine_repo
from planned.services import planning_svc
from planned.utils.dates import get_current_date

router = APIRouter()


@router.get("/routines")
async def list_routines() -> list[Routine]:
    return await routine_repo.all()


@router.get("/preview/today")
async def preview_today() -> DayContext:
    return await planning_svc.preview(get_current_date())


@router.get("/preview/{date}")
async def preview_date(date: datetime.date) -> DayContext:
    return await planning_svc.preview(date)
