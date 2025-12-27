"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.

Services are resolved from the DI container stored in app state.
"""

from typing import Annotated

from fastapi import Depends, Request

from planned.application.services import AuthService, CalendarService, DayService, PlanningService
from planned.core.di.container import DIContainer
from planned.infrastructure.utils.dates import get_current_date
from ..repositories import get_container


def get_auth_service() -> AuthService:
    """Get an instance of AuthService."""
    # AuthService has no dependencies, so create directly
    return AuthService()


def get_calendar_service(
    container: Annotated[DIContainer, Depends(get_container)]
) -> CalendarService:
    """Get an instance of CalendarService from the DI container."""
    return container.get(CalendarService)


def get_planning_service(
    container: Annotated[DIContainer, Depends(get_container)]
) -> PlanningService:
    """Get an instance of PlanningService from the DI container."""
    return container.get(PlanningService)


async def get_day_service_for_current_date(
    container: Annotated[DIContainer, Depends(get_container)]
) -> DayService:
    """Get an instance of DayService for today's date."""
    from planned.application.repositories import (
        DayRepositoryProtocol,
        DayTemplateRepositoryProtocol,
        EventRepositoryProtocol,
        MessageRepositoryProtocol,
        TaskRepositoryProtocol,
    )
    from planned.application.services import DayService

    from typing import cast

    day_repo = cast(DayRepositoryProtocol, container.get(DayRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    day_template_repo = cast(DayTemplateRepositoryProtocol, container.get(DayTemplateRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    event_repo = cast(EventRepositoryProtocol, container.get(EventRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    message_repo = cast(MessageRepositoryProtocol, container.get(MessageRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    task_repo = cast(TaskRepositoryProtocol, container.get(TaskRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]

    return await DayService.for_date(
        get_current_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )
