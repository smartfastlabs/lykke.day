"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

import datetime
from typing import Annotated

from fastapi import Depends, Request

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
from planned.application.services import (
    CalendarService,
    DayService,
    PlanningService,
    SheppardManager,
    SheppardService,
)
from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.infrastructure.gateways.adapters import GoogleCalendarGatewayAdapter
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

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
    get_user_repo,
)
from ..user import get_current_user


def get_calendar_service(
    user: Annotated[User, Depends(get_current_user)],
    auth_token_repo: Annotated[
        AuthTokenRepositoryProtocol, Depends(get_auth_token_repo)
    ],
    calendar_repo: Annotated[CalendarRepositoryProtocol, Depends(get_calendar_repo)],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
) -> CalendarService:
    """Get an instance of CalendarService."""
    google_gateway = GoogleCalendarGatewayAdapter()
    return CalendarService(
        user=user,
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
        google_gateway=google_gateway,
    )


def get_planning_service(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    routine_repo: Annotated[RoutineRepositoryProtocol, Depends(get_routine_repo)],
    task_definition_repo: Annotated[
        TaskDefinitionRepositoryProtocol, Depends(get_task_definition_repo)
    ],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> PlanningService:
    """Get a user-scoped instance of PlanningService."""
    return PlanningService(
        user=user,
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
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Get a user-scoped instance of DayService for today's date."""
    return await get_day_service_for_date(
        get_current_date(),
        user=user,
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def get_day_service_for_tomorrow_date(
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Get a user-scoped instance of DayService for tomorrow's date."""
    return await get_day_service_for_date(
        get_tomorrows_date(),
        user=user,
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def get_day_service_for_date(
    date: datetime.date,
    user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repo)],
    day_repo: Annotated[DayRepositoryProtocol, Depends(get_day_repo)],
    day_template_repo: Annotated[
        DayTemplateRepositoryProtocol, Depends(get_day_template_repo)
    ],
    event_repo: Annotated[EventRepositoryProtocol, Depends(get_event_repo)],
    message_repo: Annotated[MessageRepositoryProtocol, Depends(get_message_repo)],
    task_repo: Annotated[TaskRepositoryProtocol, Depends(get_task_repo)],
) -> DayService:
    """Get a user-scoped instance of DayService for a specific date."""
    # Create a temporary DayService instance to load context
    template_slug = user.settings.template_defaults[date.weekday()]
    template = await day_template_repo.get_by_slug(template_slug)
    temp_day = await DayService.base_day(
        date,
        user_id=user.id,
        template=template,
    )
    from planned.domain.value_objects.day import DayContext

    temp_ctx = DayContext(day=temp_day)
    temp_day_svc = DayService(
        user=user,
        ctx=temp_ctx,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )
    ctx = await temp_day_svc.load_context(
        date=date,
        user_id=user.id,
        user_repo=user_repo,
    )
    return DayService(
        user=user,
        ctx=ctx,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )


async def get_sheppard_service(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> SheppardService:
    """Get the SheppardService instance for the logged-in user.

    Args:
        request: FastAPI request object (to access app state)
        user: Current user (from dependency)

    Returns:
        SheppardService instance for the user

    Raises:
        RuntimeError: If SheppardManager is not available or service doesn't exist
    """
    # Get SheppardManager from app state
    manager: SheppardManager | None = getattr(
        request.app.state, "sheppard_manager", None
    )
    if manager is None:
        raise exceptions.ServerError(
            "SheppardManager is not available. The service may not be initialized."
        )

    user_id = user.id
    try:
        service = await manager.ensure_service_for_user(user_id)
    except RuntimeError as e:
        raise exceptions.ServerError(
            f"SheppardService is not available for user {user_id}: {e}"
        ) from e

    return service
