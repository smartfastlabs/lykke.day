import datetime
from fastapi import Depends

from planned.services import DayService, SheppardService
from planned.utils.dates import get_current_date

from ..dependencies.repositories import (
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_push_subscription_repo,
    get_task_repo,
)
from ..dependencies.services import get_calendar_service, get_planning_service
from .days import load_todays_day_svc


async def load_sheppard_svc(
    date: datetime.date,
    day_svc: DayService = Depends(load_todays_day_svc),
    push_subscription_repo=Depends(get_push_subscription_repo),
    task_repo=Depends(get_task_repo),
    calendar_service=Depends(get_calendar_service),
    planning_service=Depends(get_planning_service),
    day_repo=Depends(get_day_repo),
    day_template_repo=Depends(get_day_template_repo),
    event_repo=Depends(get_event_repo),
    message_repo=Depends(get_message_repo),
) -> SheppardService:
    """Load SheppardService with all required dependencies."""
    push_subscriptions = await push_subscription_repo.all()
    
    return SheppardService(
        day_svc=day_svc,
        push_subscription_repo=push_subscription_repo,
        task_repo=task_repo,
        calendar_service=calendar_service,
        planning_service=planning_service,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        push_subscriptions=push_subscriptions,
    )
