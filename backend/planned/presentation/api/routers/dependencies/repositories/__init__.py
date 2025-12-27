"""
Repository dependency injection functions.

Each function returns a new instance of a repository, which can be used
with FastAPI's Depends() in route handlers.
"""

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


def get_auth_token_repo() -> AuthTokenRepository:
    """Get an instance of AuthTokenRepository."""
    return AuthTokenRepository()


def get_calendar_repo() -> CalendarRepository:
    """Get an instance of CalendarRepository."""
    return CalendarRepository()


def get_day_repo() -> DayRepository:
    """Get an instance of DayRepository."""
    return DayRepository()


def get_day_template_repo() -> DayTemplateRepository:
    """Get an instance of DayTemplateRepository."""
    return DayTemplateRepository()


def get_event_repo() -> EventRepository:
    """Get an instance of EventRepository."""
    return EventRepository()


def get_message_repo() -> MessageRepository:
    """Get an instance of MessageRepository."""
    return MessageRepository()


def get_push_subscription_repo() -> PushSubscriptionRepository:
    """Get an instance of PushSubscriptionRepository."""
    return PushSubscriptionRepository()


def get_routine_repo() -> RoutineRepository:
    """Get an instance of RoutineRepository."""
    return RoutineRepository()


def get_task_repo() -> TaskRepository:
    """Get an instance of TaskRepository."""
    return TaskRepository()


def get_task_definition_repo() -> TaskDefinitionRepository:
    """Get an instance of TaskDefinitionRepository."""
    return TaskDefinitionRepository()
