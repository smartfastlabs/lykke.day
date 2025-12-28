import datetime
from typing import Annotated

from fastapi import Depends

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.application.services import CalendarService, DayService, PlanningService, SheppardService
from planned.infrastructure.gateways.adapters import WebPushGatewayAdapter

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
    day_svc: Annotated[DayService, Depends(load_todays_day_svc)],
    push_subscription_repo: Annotated[PushSubscriptionRepositoryProtocol, Depends(get_push_subscription_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
    calendar_service: Annotated[CalendarService, Depends(get_calendar_service)],
    planning_service: Annotated[PlanningService, Depends(get_planning_service)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
) -> SheppardService:
    """Load SheppardService with all required dependencies."""
    push_subscriptions = await push_subscription_repo.all()
    web_push_gateway = WebPushGatewayAdapter()
    
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
        web_push_gateway=web_push_gateway,
        push_subscriptions=push_subscriptions,
    )
