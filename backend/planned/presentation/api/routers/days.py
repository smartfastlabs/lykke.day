import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.application.services import DayService, PlanningService
from planned.core.exceptions import exceptions
from planned.domain.entities import Day, DayContext, DayStatus, DayTemplate, User
from planned.domain.value_objects.base import BaseRequestObject
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from .dependencies.repositories import (
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_task_repo,
)
from .dependencies.services import get_planning_service
from .dependencies.user import get_current_user, get_user_repo

router = APIRouter()


@router.put("/today/schedule")
async def schedule_today(
    user: Annotated[User, Depends(get_current_user)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
) -> DayContext:
    result = await planning_service.schedule(get_current_date())
    return result


async def _get_context_for_date(
    date: datetime.date,
    user: User,
    user_repo: UserRepositoryProtocol,
    planning_service: PlanningService,
    day_repo: DayRepositoryProtocol,
    day_template_repo: DayTemplateRepositoryProtocol,
    event_repo: EventRepositoryProtocol,
    message_repo: MessageRepositoryProtocol,
    task_repo: TaskRepositoryProtocol,
) -> DayContext:
    """Helper function to get context for a specific date."""
    from uuid import UUID

    day_svc: DayService = await DayService.for_date(
        date,
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        user_repo=user_repo,
    )
    if day_svc.ctx.day.status != DayStatus.SCHEDULED:
        return await planning_service.schedule(day_svc.ctx.day.date)

    return day_svc.ctx


@router.get("/today/context")
async def get_context_today(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayContext:
    return await _get_context_for_date(
        get_current_date(),
        user,
        user_repo,
        planning_service,
        day_repo,
        day_template_repo,
        event_repo,
        message_repo,
        task_repo,
    )


@router.get("/tomorrow/context")
async def get_context_tomorrow(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayContext:
    return await _get_context_for_date(
        get_tomorrows_date(),
        user,
        user_repo,
        planning_service,
        day_repo,
        day_template_repo,
        event_repo,
        message_repo,
        task_repo,
    )


@router.get("/{date}/context")
async def get_context(
    date: datetime.date,
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayContext:
    return await _get_context_for_date(
        date,
        user,
        user_repo,
        planning_service,
        day_repo,
        day_template_repo,
        event_repo,
        message_repo,
        task_repo,
    )


class UpdateDayRequest(BaseRequestObject):
    status: DayStatus | None = None
    template_id: str | None = None


@router.patch("/{date}")
async def update_day(
    date: datetime.date,
    request: UpdateDayRequest,
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
) -> Day:
    from uuid import UUID

    day: Day = await DayService.get_or_preview(
        date,
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    if request.status is not None:
        day.status = request.status
    if request.template_id is not None:
        day.template_id = request.template_id
    return await day_repo.put(day)


@router.get("/templates")
async def get_templates(
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
) -> list[DayTemplate]:
    return await day_template_repo.all()
