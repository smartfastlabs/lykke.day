import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.application.services import DayService
from planned.domain.entities import User
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from ..dependencies.repositories import (
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_task_repo,
)
from ..dependencies.user import get_current_user


async def load_day_svc(
    date: datetime.date,
    user: Annotated[User, Depends(get_current_user)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for a specific date."""
    return await DayService.for_date(
        date,
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def load_todays_day_svc(
    user: Annotated[User, Depends(get_current_user)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for today's date."""
    return await DayService.for_date(
        get_current_date(),
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def load_tomorrows_day_svc(
    user: Annotated[User, Depends(get_current_user)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for tomorrow's date."""
    return await DayService.for_date(
        get_tomorrows_date(),
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )
