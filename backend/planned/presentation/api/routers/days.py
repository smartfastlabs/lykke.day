import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from planned.application.services import DayService, PlanningService
from planned.domain.entities import Day, DayContext, DayStatus, DayTemplate
from planned.domain.value_objects.base import BaseRequestObject
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.container import RepositoryContainer, get_repository_container
from .dependencies.services import (
    get_day_service_for_current_date,
    get_day_service_for_date,
    get_day_service_for_tomorrow_date,
    get_planning_service,
)

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today(
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
) -> DayContext:
    result = await planning_service.schedule(get_current_date())
    return result


@router.get("/today/context")
async def get_context_today(
    day_service: Annotated[DayService, Depends(get_day_service_for_current_date)],
) -> DayContext:
    return day_service.ctx


@router.get("/tomorrow/context")
async def get_context_tomorrow(
    day_service: Annotated[DayService, Depends(get_day_service_for_tomorrow_date)],
) -> DayContext:
    return day_service.ctx


@router.get("/{date}/context")
async def get_context(
    date: datetime.date,
    day_service: Annotated[DayService, Depends(get_day_service_for_date)],
) -> DayContext:
    return day_service.ctx


class UpdateDayRequest(BaseRequestObject):
    status: DayStatus | None = None
    template_id: UUID | None = None


@router.patch("/{date}")
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    repos: Annotated[RepositoryContainer, Depends(get_repository_container)],
) -> Day:
    """Update a day's status or template."""
    # Create a DayService instance to use get_or_preview
    # Create a temporary DayService instance to load context
    template_slug = repos.user.settings.template_defaults[date.weekday()]
    template = await repos.day_template_repo.get_by_slug(template_slug)
    temp_day = await DayService.base_day(
        date,
        user_id=repos.user.id,
        template=template,
    )
    temp_ctx = DayContext(day=temp_day)
    temp_day_svc = DayService(
        user=repos.user,
        ctx=temp_ctx,
        day_repo=repos.day_repo,
        day_template_repo=repos.day_template_repo,
        event_repo=repos.event_repo,
        message_repo=repos.message_repo,
        task_repo=repos.task_repo,
    )
    ctx = await temp_day_svc.load_context(
        date=date,
        user_id=repos.user.id,
        user_repo=repos.user_repo,
    )
    day_svc = DayService(
        user=repos.user,
        ctx=ctx,
        day_repo=repos.day_repo,
        day_template_repo=repos.day_template_repo,
        event_repo=repos.event_repo,
        message_repo=repos.message_repo,
        task_repo=repos.task_repo,
    )
    day: Day = await day_svc.get_or_preview(
        date,
        user=repos.user,
        user_repo=repos.user_repo,
    )
    if request.status is not None:
        day.status = request.status
    if request.template_id is not None:
        template = await repos.day_template_repo.get(request.template_id)
        day.template = template
    return await repos.day_repo.put(day)


@router.get("/templates")
async def get_templates(
    repos: Annotated[RepositoryContainer, Depends(get_repository_container)],
) -> list[DayTemplate]:
    return await repos.day_template_repo.all()
