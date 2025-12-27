"""
Repository dependency injection functions.

Each function returns a repository instance from the DI container,
which can be used with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast

from fastapi import Depends, Request

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.core.di.container import DIContainer


def get_container(request: Request) -> DIContainer:
    """Get the DI container from app state."""
    return cast(DIContainer, request.app.state.container)


def get_auth_token_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> AuthTokenRepositoryProtocol:
    """Get an instance of AuthTokenRepository from the DI container."""
    return cast(AuthTokenRepositoryProtocol, container.get(AuthTokenRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_calendar_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> CalendarRepositoryProtocol:
    """Get an instance of CalendarRepository from the DI container."""
    return cast(CalendarRepositoryProtocol, container.get(CalendarRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_day_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> DayRepositoryProtocol:
    """Get an instance of DayRepository from the DI container."""
    return cast(DayRepositoryProtocol, container.get(DayRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_day_template_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> DayTemplateRepositoryProtocol:
    """Get an instance of DayTemplateRepository from the DI container."""
    return cast(DayTemplateRepositoryProtocol, container.get(DayTemplateRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_event_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> EventRepositoryProtocol:
    """Get an instance of EventRepository from the DI container."""
    return cast(EventRepositoryProtocol, container.get(EventRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_message_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> MessageRepositoryProtocol:
    """Get an instance of MessageRepository from the DI container."""
    return cast(MessageRepositoryProtocol, container.get(MessageRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_push_subscription_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> PushSubscriptionRepositoryProtocol:
    """Get an instance of PushSubscriptionRepository from the DI container."""
    return cast(PushSubscriptionRepositoryProtocol, container.get(PushSubscriptionRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_routine_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> RoutineRepositoryProtocol:
    """Get an instance of RoutineRepository from the DI container."""
    return cast(RoutineRepositoryProtocol, container.get(RoutineRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_task_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> TaskRepositoryProtocol:
    """Get an instance of TaskRepository from the DI container."""
    return cast(TaskRepositoryProtocol, container.get(TaskRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]


def get_task_definition_repo(
    container: Annotated[DIContainer, Depends(get_container)]
) -> TaskDefinitionRepositoryProtocol:
    """Get an instance of TaskDefinitionRepository from the DI container."""
    return cast(TaskDefinitionRepositoryProtocol, container.get(TaskDefinitionRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
