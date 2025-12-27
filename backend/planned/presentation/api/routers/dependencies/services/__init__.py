"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.

Services will depend on repositories, which are also injected via Depends().
"""

from typing import Annotated

from fastapi import Depends

from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)
from planned.presentation.api.routers.dependencies.repositories import (
    get_auth_token_repo,
    get_calendar_repo,
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_push_subscription_repo,
    get_routine_repo,
    get_task_definition_repo,
    get_task_repo,
)
from planned.application.services import AuthService, CalendarService, DayService, PlanningService
from planned.infrastructure.utils.dates import get_current_date


def get_auth_service() -> AuthService:
    """Get an instance of AuthService."""
    return AuthService()


def get_calendar_service(
    auth_token_repo: Annotated[AuthTokenRepository, Depends(get_auth_token_repo)],
    calendar_repo: Annotated[CalendarRepository, Depends(get_calendar_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
) -> CalendarService:
    """Get an instance of CalendarService."""
    return CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
    )


async def get_day_service_for_current_date(
    day_repo: Annotated[DayRepository, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepository, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepository, Depends(get_task_repo)],
) -> DayService:
    """Get an instance of DayService for today's date."""
    return await DayService.for_date(
        get_current_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


def get_planning_service(
    day_repo: Annotated[DayRepository, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepository, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepository, Depends(get_message_repo)],
    routine_repo: Annotated[RoutineRepository, Depends(get_routine_repo)],
    task_definition_repo: Annotated[
        TaskDefinitionRepository, Depends(get_task_definition_repo)
    ],
    task_repo: Annotated[TaskRepository, Depends(get_task_repo)],
) -> PlanningService:
    """Get an instance of PlanningService."""
    return PlanningService(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )
