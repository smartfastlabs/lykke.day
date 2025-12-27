import datetime
from typing import Annotated

from fastapi import Depends

from planned.infrastructure.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    TaskRepository,
)
from planned.application.services import DayService
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from ..dependencies.repositories import (
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_task_repo,
)


async def load_day_svc(
    date: datetime.date,
    day_repo: Annotated[DayRepository, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepository, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepository, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for a specific date."""
    return await DayService.for_date(
        date,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def load_todays_day_svc(
    day_repo: Annotated[DayRepository, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepository, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepository, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for today's date."""
    return await DayService.for_date(
        get_current_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def load_tomorrows_day_svc(
    day_repo: Annotated[DayRepository, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepository, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepository, Depends(get_task_repo)],
) -> DayService:
    """Load DayService for tomorrow's date."""
    return await DayService.for_date(
        get_tomorrows_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )
