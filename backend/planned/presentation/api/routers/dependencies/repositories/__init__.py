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
    from uuid import UUID

    return cast(
        "AuthTokenRepositoryProtocol", AuthTokenRepository(user_uuid=UUID(user.id))
    )


def get_calendar_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> CalendarRepositoryProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    from uuid import UUID

    return cast(
        "CalendarRepositoryProtocol", CalendarRepository(user_uuid=UUID(user.id))
    )


def get_day_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> DayRepositoryProtocol:
    """Get a user-scoped instance of DayRepository."""
    from uuid import UUID

    return cast("DayRepositoryProtocol", DayRepository(user_uuid=UUID(user.id)))


def get_day_template_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> DayTemplateRepositoryProtocol:
    """Get a user-scoped instance of DayTemplateRepository."""
    from uuid import UUID

    return cast(
        "DayTemplateRepositoryProtocol", DayTemplateRepository(user_uuid=UUID(user.id))
    )


def get_event_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> EventRepositoryProtocol:
    """Get a user-scoped instance of EventRepository."""
    from uuid import UUID

    return cast("EventRepositoryProtocol", EventRepository(user_uuid=UUID(user.id)))


def get_message_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> MessageRepositoryProtocol:
    """Get a user-scoped instance of MessageRepository."""
    from uuid import UUID

    return cast("MessageRepositoryProtocol", MessageRepository(user_uuid=UUID(user.id)))


def get_push_subscription_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> PushSubscriptionRepositoryProtocol:
    """Get a user-scoped instance of PushSubscriptionRepository."""
    from uuid import UUID

    return cast(
        "PushSubscriptionRepositoryProtocol",
        PushSubscriptionRepository(user_uuid=UUID(user.id)),
    )


def get_routine_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> RoutineRepositoryProtocol:
    """Get a user-scoped instance of RoutineRepository."""
    from uuid import UUID

    return cast("RoutineRepositoryProtocol", RoutineRepository(user_uuid=UUID(user.id)))


def get_task_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> TaskRepositoryProtocol:
    """Get a user-scoped instance of TaskRepository."""
    from uuid import UUID

    return cast("TaskRepositoryProtocol", TaskRepository(user_uuid=UUID(user.id)))


def get_task_definition_repo(
    user: Annotated[User, Depends(get_current_user)],
) -> TaskDefinitionRepositoryProtocol:
    """Get a user-scoped instance of TaskDefinitionRepository."""
    from uuid import UUID

    return cast(
        "TaskDefinitionRepositoryProtocol",
        TaskDefinitionRepository(user_uuid=UUID(user.id)),
    )
