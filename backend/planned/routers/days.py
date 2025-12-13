import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter, Depends

from planned import exceptions
from planned.objects import BaseObject, Day, DayContext, DayStatus, DayTemplate
from planned.repositories import day_repo, day_template_repo, event_repo, task_repo
from planned.services import DayService, planning_svc
from planned.utils.dates import get_current_date, get_tomorrows_date

from .helpers.days import load_todays_day_svc, load_tomorrows_day_svc

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today() -> DayContext:
    return await planning_svc.schedule(get_current_date())


@router.get("/{date}/context")
async def get_context(
    date: datetime.date | Literal["today", "tomorrow"],
) -> DayContext:
    if isinstance(date, str):
        if date == "today":
            date = get_current_date()
        elif date == "tomorrow":
            date = get_tomorrows_date()

        else:
            raise exceptions.BadRequestError("invalid date")

    day_svc: DayService = await DayService.for_date(date)
    if day_svc.ctx.day.status != DayStatus.SCHEDULED:
        return await planning_svc.schedule(day_svc.ctx.day.date)

    return day_svc.ctx


class UpdateDayRequest(BaseObject):
    status: DayStatus | None = None
    template_id: str | None = None


@router.patch("/{date}")
async def update_day(date: datetime.date, request: UpdateDayRequest) -> Day:
    day: Day = await DayService.get_or_preview(date)
    if request.status is not None:
        day.status = request.status
    if request.template_id is not None:
        day.template_id = request.template_id
    return await day_repo.put(day)


@router.get("/templates")
async def get_templates() -> list[DayTemplate]:
    return await day_template_repo.all()
