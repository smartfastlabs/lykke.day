"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast

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
from planned.domain.entities import User
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

from ..user import get_current_user


def get_auth_token_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> AuthTokenRepositoryProtocol:
    """Get a user-scoped instance of AuthTokenRepository."""
    return cast(
        "AuthTokenRepositoryProtocol", AuthTokenRepository(user_uuid=user.uuid)
    )


def get_calendar_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> CalendarRepositoryProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    return cast(
        "CalendarRepositoryProtocol", CalendarRepository(user_uuid=user.uuid)
    )


def get_day_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> DayRepositoryProtocol:
    """Get a user-scoped instance of DayRepository."""
    return cast("DayRepositoryProtocol", DayRepository(user_uuid=user.uuid))


def get_day_template_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> DayTemplateRepositoryProtocol:
    """Get a user-scoped instance of DayTemplateRepository."""
    return cast(
        "DayTemplateRepositoryProtocol", DayTemplateRepository(user_uuid=user.uuid)
    )


def get_event_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> EventRepositoryProtocol:
    """Get a user-scoped instance of EventRepository."""
    return cast("EventRepositoryProtocol", EventRepository(user_uuid=user.uuid))


def get_message_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> MessageRepositoryProtocol:
    """Get a user-scoped instance of MessageRepository."""
    return cast("MessageRepositoryProtocol", MessageRepository(user_uuid=user.uuid))


def get_push_subscription_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> PushSubscriptionRepositoryProtocol:
    """Get a user-scoped instance of PushSubscriptionRepository."""
    return cast(
        "PushSubscriptionRepositoryProtocol",
        PushSubscriptionRepository(user_uuid=user.uuid),
    )


def get_routine_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> RoutineRepositoryProtocol:
    """Get a user-scoped instance of RoutineRepository."""
    return cast("RoutineRepositoryProtocol", RoutineRepository(user_uuid=user.uuid))


def get_task_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> TaskRepositoryProtocol:
    """Get a user-scoped instance of TaskRepository."""
    return cast("TaskRepositoryProtocol", TaskRepository(user_uuid=user.uuid))


def get_task_definition_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> TaskDefinitionRepositoryProtocol:
    """Get a user-scoped instance of TaskDefinitionRepository."""
    return cast(
        "TaskDefinitionRepositoryProtocol",
        TaskDefinitionRepository(user_uuid=user.uuid),
    )
