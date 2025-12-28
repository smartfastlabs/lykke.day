"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated

from fastapi import Depends

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.application.services import AuthService, CalendarService, DayService, PlanningService
from planned.domain.entities import User
from planned.infrastructure.gateways.adapters import GoogleCalendarGatewayAdapter
from planned.infrastructure.utils.dates import get_current_date
from ..repositories import (
    get_auth_token_repo,
    get_calendar_repo,
    get_day_repo,
    get_day_template_repo,
    get_event_repo,
    get_message_repo,
    get_routine_repo,
    get_task_definition_repo,
    get_task_repo,
)
from ..user import get_current_user, get_user_repo


def get_auth_service(
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
) -> AuthService:
    """Get an instance of AuthService."""
    return AuthService(user_repo=user_repo)


def get_calendar_service(
    auth_token_repo: Annotated[AuthTokenRepositoryProtocol, Depends(get_auth_token_repo)],
    calendar_repo: Annotated[CalendarRepositoryProtocol, Depends(get_calendar_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
) -> CalendarService:
    """Get an instance of CalendarService."""
    google_gateway = GoogleCalendarGatewayAdapter()
    return CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
        google_gateway=google_gateway,
    )


def get_planning_service(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    routine_repo: Annotated[RoutineRepositoryProtocol, Depends(get_routine_repo)],
    task_definition_repo: Annotated[TaskDefinitionRepositoryProtocol, Depends(get_task_definition_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> PlanningService:
    """Get a user-scoped instance of PlanningService."""
    from uuid import UUID
    return PlanningService(
        user_uuid=UUID(user.id),
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )


async def get_day_service_for_current_date(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[DayTemplateRepositoryProtocol, Depends(get_day_template_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Get a user-scoped instance of DayService for today's date."""
    from uuid import UUID
    return await DayService.for_date(
        get_current_date(),
        user_uuid=UUID(user.id),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        user_repo=user_repo,
    )
