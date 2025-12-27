"""
Repository dependency injection functions.

Each function returns a repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from functools import lru_cache
from typing import Annotated

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


@lru_cache()
def get_auth_token_repo() -> AuthTokenRepositoryProtocol:
    """Get an instance of AuthTokenRepository."""
    return AuthTokenRepository()


@lru_cache()
def get_calendar_repo() -> CalendarRepositoryProtocol:
    """Get an instance of CalendarRepository."""
    return CalendarRepository()


@lru_cache()
def get_day_repo() -> DayRepositoryProtocol:
    """Get an instance of DayRepository."""
    return DayRepository()


@lru_cache()
def get_day_template_repo() -> DayTemplateRepositoryProtocol:
    """Get an instance of DayTemplateRepository."""
    return DayTemplateRepository()


@lru_cache()
def get_event_repo() -> EventRepositoryProtocol:
    """Get an instance of EventRepository."""
    return EventRepository()


@lru_cache()
def get_message_repo() -> MessageRepositoryProtocol:
    """Get an instance of MessageRepository."""
    return MessageRepository()


@lru_cache()
def get_push_subscription_repo() -> PushSubscriptionRepositoryProtocol:
    """Get an instance of PushSubscriptionRepository."""
    return PushSubscriptionRepository()


@lru_cache()
def get_routine_repo() -> RoutineRepositoryProtocol:
    """Get an instance of RoutineRepository."""
    return RoutineRepository()


@lru_cache()
def get_task_repo() -> TaskRepositoryProtocol:
    """Get an instance of TaskRepository."""
    return TaskRepository()


@lru_cache()
def get_task_definition_repo() -> TaskDefinitionRepositoryProtocol:
    """Get an instance of TaskDefinitionRepository."""
    return TaskDefinitionRepository()
