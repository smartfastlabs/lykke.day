import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter, Depends

from planned.objects import BaseObject, Day, DayContext, DayStatus
from planned.repositories import day_repo, event_repo, task_repo
from planned.services import DayService, planning_svc
from planned.utils.dates import get_current_date

from .helpers.days import load_todays_day_svc

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today() -> DayContext:
    return await planning_svc.schedule(get_current_date())


@router.get("/today")
async def get_today(day_svc: DayService = Depends(load_todays_day_svc)) -> DayContext:
    if day_svc.ctx.day.status != DayStatus.SCHEDULED:
        return await planning_svc.schedule(day_svc.ctx.day.date)

    return day_svc.ctx


class UpdateDayRequest(BaseObject):
    status: DayStatus | None = None


@router.patch("/{date}")
async def update_day(date: datetime.date, request: UpdateDayRequest) -> Day:
    day: Day = await DayService.get_or_preview(date)
    if request.status is not None:
        day.status = request.status
    return await day_repo.put(day)
