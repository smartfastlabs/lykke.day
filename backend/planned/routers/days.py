import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date

from fastapi import APIRouter, Depends

from planned import exceptions
from planned.objects import BaseRequestObject, Day, DayContext, DayStatus, DayTemplate
from planned.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    TaskRepository,
)
from planned.services import DayService, PlanningService
from planned.utils.dates import get_current_date, get_tomorrows_date

from .dependencies.repositories import (
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_task_repo,
)
from .dependencies.services import get_planning_service

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today(
    planning_service: PlanningService = Depends(get_planning_service),
) -> DayContext:
    return await planning_service.schedule(get_current_date())


@router.get("/{date}/context")
async def get_context(
    date: datetime.date | Literal["today", "tomorrow"],
    planning_service: PlanningService = Depends(get_planning_service),
    day_repo: DayRepository = Depends(get_day_repo),
    day_template_repo: DayTemplateRepository = Depends(get_day_template_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    task_repo: TaskRepository = Depends(get_task_repo),
) -> DayContext:
    if isinstance(date, str):
        if date == "today":
            date = get_current_date()
        elif date == "tomorrow":
            date = get_tomorrows_date()
        else:
            raise exceptions.BadRequestError("invalid date")

    day_svc: DayService = await DayService.for_date(
        date,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )
    if day_svc.ctx.day.status != DayStatus.SCHEDULED:
        return await planning_service.schedule(day_svc.ctx.day.date)

    return day_svc.ctx


class UpdateDayRequest(BaseRequestObject):
    status: DayStatus | None = None
    template_id: str | None = None


@router.patch("/{date}")
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    day_repo: DayRepository = Depends(get_day_repo),
    day_template_repo: DayTemplateRepository = Depends(get_day_template_repo),
) -> Day:
    day: Day = await DayService.get_or_preview(
        date,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
    )
    if request.status is not None:
        day.status = request.status
    if request.template_id is not None:
        day.template_id = request.template_id
    return await day_repo.put(day)


@router.get("/templates")
async def get_templates(
    day_template_repo: DayTemplateRepository = Depends(get_day_template_repo),
) -> list[DayTemplate]:
    return await day_template_repo.all()
