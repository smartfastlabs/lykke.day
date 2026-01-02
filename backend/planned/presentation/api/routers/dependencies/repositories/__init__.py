"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast

from fastapi import Depends

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarEntryRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.domain import entities
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntryRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    UserRepository,
)

from ..user import get_current_user


def get_auth_token_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> AuthTokenRepositoryProtocol:
    """Get an instance of AuthTokenRepository (not user-scoped)."""
    return cast(
        "AuthTokenRepositoryProtocol", AuthTokenRepository()
    )


def get_calendar_entry_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> CalendarEntryRepositoryProtocol:
    """Get a user-scoped instance of CalendarEntryRepository."""
    return cast("CalendarEntryRepositoryProtocol", CalendarEntryRepository(user_id=user.id))


def get_calendar_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> CalendarRepositoryProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    return cast(
        "CalendarRepositoryProtocol", CalendarRepository(user_id=user.id)
    )


def get_day_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> DayRepositoryProtocol:
    """Get a user-scoped instance of DayRepository."""
    return cast("DayRepositoryProtocol", DayRepository(user_id=user.id))


def get_day_template_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> DayTemplateRepositoryProtocol:
    """Get a user-scoped instance of DayTemplateRepository."""
    return cast(
        "DayTemplateRepositoryProtocol", DayTemplateRepository(user_id=user.id)
    )


def get_message_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> MessageRepositoryProtocol:
    """Get a user-scoped instance of MessageRepository."""
    return cast("MessageRepositoryProtocol", MessageRepository(user_id=user.id))


def get_push_subscription_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> PushSubscriptionRepositoryProtocol:
    """Get a user-scoped instance of PushSubscriptionRepository."""
    return cast(
        "PushSubscriptionRepositoryProtocol",
        PushSubscriptionRepository(user_id=user.id),
    )


def get_routine_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> RoutineRepositoryProtocol:
    """Get a user-scoped instance of RoutineRepository."""
    return cast("RoutineRepositoryProtocol", RoutineRepository(user_id=user.id))


def get_task_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> TaskRepositoryProtocol:
    """Get a user-scoped instance of TaskRepository."""
    return cast("TaskRepositoryProtocol", TaskRepository(user_id=user.id))


def get_task_definition_repo(
    user: Annotated[entities.User, Depends(get_current_user)],
) -> TaskDefinitionRepositoryProtocol:
    """Get a user-scoped instance of TaskDefinitionRepository."""
    return cast(
        "TaskDefinitionRepositoryProtocol",
        TaskDefinitionRepository(user_id=user.id),
    )


def get_user_repo() -> UserRepositoryProtocol:
    """Get an instance of UserRepository (not user-scoped)."""
    return cast("UserRepositoryProtocol", UserRepository())
