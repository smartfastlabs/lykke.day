"""
Repository dependency injection functions.

Each function returns a repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import cast

from fastapi import Depends

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
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)


def get_auth_token_repo() -> AuthTokenRepositoryProtocol:
    """Get an instance of AuthTokenRepository."""
    return cast(AuthTokenRepositoryProtocol, AuthTokenRepository())


def get_calendar_repo() -> CalendarRepositoryProtocol:
    """Get an instance of CalendarRepository."""
    return cast(CalendarRepositoryProtocol, CalendarRepository())


def get_day_repo() -> DayRepositoryProtocol:
    """Get an instance of DayRepository."""
    return cast(DayRepositoryProtocol, DayRepository())


def get_day_template_repo() -> DayTemplateRepositoryProtocol:
    """Get an instance of DayTemplateRepository."""
    return cast(DayTemplateRepositoryProtocol, DayTemplateRepository())


def get_event_repo() -> EventRepositoryProtocol:
    """Get an instance of EventRepository."""
    return cast(EventRepositoryProtocol, EventRepository())


def get_message_repo() -> MessageRepositoryProtocol:
    """Get an instance of MessageRepository."""
    return cast(MessageRepositoryProtocol, MessageRepository())


def get_push_subscription_repo() -> PushSubscriptionRepositoryProtocol:
    """Get an instance of PushSubscriptionRepository."""
    return cast(PushSubscriptionRepositoryProtocol, PushSubscriptionRepository())


def get_routine_repo() -> RoutineRepositoryProtocol:
    """Get an instance of RoutineRepository."""
    return cast(RoutineRepositoryProtocol, RoutineRepository())


def get_task_repo() -> TaskRepositoryProtocol:
    """Get an instance of TaskRepository."""
    return cast(TaskRepositoryProtocol, TaskRepository())


def get_task_definition_repo() -> TaskDefinitionRepositoryProtocol:
    """Get an instance of TaskDefinitionRepository."""
    return cast(TaskDefinitionRepositoryProtocol, TaskDefinitionRepository())
