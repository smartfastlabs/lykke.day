import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from planned.application.services import DayService, PlanningService
from planned.application.services.factories import DayServiceFactory
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import Day, DayContext, DayStatus, DayTemplate
from planned.domain.value_objects.base import BaseRequestObject
from planned.infrastructure.utils.dates import get_current_date

from .dependencies.container import RepositoryContainer, get_repository_container
from .dependencies.services import (
    get_day_service_for_current_date,
    get_day_service_for_date,
    get_day_service_for_tomorrow_date,
    get_planning_service,
    get_unit_of_work_factory,
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
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> Day:
    """Update a day's status or template."""
    # Use factory to create DayService
    factory = DayServiceFactory(
        user=repos.user,
        uow_factory=uow_factory,
    )
    day_svc = await factory.create(date, user_id=repos.user.id)

    # Get or preview the day
    day: Day = await day_svc.get_or_preview(date)

    # Update day using domain methods and save
    uow = uow_factory.create(repos.user.id)
    async with uow:
        # Reload day in UoW context
        day = await uow.days.get(day.id)

        if request.status is not None:
            if request.status == DayStatus.SCHEDULED and day.template:
                day.schedule(day.template)
            elif request.status == DayStatus.UNSCHEDULED:
                day.unschedule()
            elif request.status == DayStatus.COMPLETE:
                day.complete()
            else:
                # For other statuses, set directly (not ideal but maintains compatibility)
                day.status = request.status

        if request.template_id is not None:
            template = await uow.day_templates.get(request.template_id)
            day.update_template(template)

        # Save and commit
        result = await uow.days.put(day)
        await uow.commit()
        return result


@router.get("/templates")
async def get_templates(
    repos: Annotated[RepositoryContainer, Depends(get_repository_container)],
) -> list[DayTemplate]:
    return await repos.day_template_repo.all()
