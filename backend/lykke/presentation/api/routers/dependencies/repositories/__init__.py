"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Path

from lykke.application.repositories import (
    AuthTokenRepositoryReadWriteProtocol,
    CalendarEntryRepositoryReadWriteProtocol,
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
    DayRepositoryReadWriteProtocol,
    DayTemplateRepositoryReadWriteProtocol,
    PushSubscriptionRepositoryReadWriteProtocol,
    RoutineRepositoryReadWriteProtocol,
    TaskDefinitionRepositoryReadWriteProtocol,
    TaskRepositoryReadWriteProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)
from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntryRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    UserRepository,
)

from ..user import get_current_user


def get_auth_token_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AuthTokenRepositoryReadWriteProtocol:
    """Get an instance of AuthTokenRepository (not user-scoped)."""
    return cast(
        "AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository()
    )


def get_calendar_entry_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CalendarEntryRepositoryReadWriteProtocol:
    """Get a user-scoped instance of CalendarEntryRepository."""
    return cast("CalendarEntryRepositoryReadWriteProtocol", CalendarEntryRepository(user_id=user.id))


def get_calendar_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CalendarRepositoryReadWriteProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    return cast(
        "CalendarRepositoryReadWriteProtocol", CalendarRepository(user_id=user.id)
    )


def get_day_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DayRepositoryReadWriteProtocol:
    """Get a user-scoped instance of DayRepository."""
    return cast("DayRepositoryReadWriteProtocol", DayRepository(user_id=user.id))


def get_day_template_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DayTemplateRepositoryReadWriteProtocol:
    """Get a user-scoped instance of DayTemplateRepository."""
    return cast(
        "DayTemplateRepositoryReadWriteProtocol", DayTemplateRepository(user_id=user.id)
    )


def get_push_subscription_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> PushSubscriptionRepositoryReadWriteProtocol:
    """Get a user-scoped instance of PushSubscriptionRepository."""
    return cast(
        "PushSubscriptionRepositoryReadWriteProtocol",
        PushSubscriptionRepository(user_id=user.id),
    )


def get_routine_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RoutineRepositoryReadWriteProtocol:
    """Get a user-scoped instance of RoutineRepository."""
    return cast("RoutineRepositoryReadWriteProtocol", RoutineRepository(user_id=user.id))


def get_task_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> TaskRepositoryReadWriteProtocol:
    """Get a user-scoped instance of TaskRepository."""
    return cast("TaskRepositoryReadWriteProtocol", TaskRepository(user_id=user.id))


def get_task_definition_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> TaskDefinitionRepositoryReadWriteProtocol:
    """Get a user-scoped instance of TaskDefinitionRepository."""
    return cast(
        "TaskDefinitionRepositoryReadWriteProtocol",
        TaskDefinitionRepository(user_id=user.id),
    )


def get_user_repo() -> UserRepositoryReadWriteProtocol:
    """Get an instance of UserRepository (not user-scoped)."""
    return cast("UserRepositoryReadWriteProtocol", UserRepository())


def get_time_block_definition_ro_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> TimeBlockDefinitionRepositoryReadOnlyProtocol:
    """Get a user-scoped instance of TimeBlockDefinitionRepository (read-only)."""
    return cast(
        "TimeBlockDefinitionRepositoryReadOnlyProtocol",
        TimeBlockDefinitionRepository(user_id=user.id),
    )


def get_calendar_repo_by_user_id(
    user_id: Annotated[UUID, Path()],
) -> CalendarRepositoryReadOnlyProtocol:
    """Get a user-scoped CalendarRepository using user_id from path (for webhooks)."""
    return cast(
        "CalendarRepositoryReadOnlyProtocol", CalendarRepository(user_id=user_id)
    )
