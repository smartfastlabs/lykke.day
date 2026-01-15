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
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    TimeBlockDefinitionRepository,
)

from ..user import get_current_user


def get_auth_token_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AuthTokenRepositoryReadWriteProtocol:
    """Get an instance of AuthTokenRepository (not user-scoped)."""
    return cast(
        "AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository()
    )


def get_calendar_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CalendarRepositoryReadWriteProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    return cast(
        "CalendarRepositoryReadWriteProtocol", CalendarRepository(user_id=user.id)
    )


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
