"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Path

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
    UserRepository,
)
from lykke.presentation.api.routers.dependencies.user import get_current_user


def get_auth_token_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AuthTokenRepositoryReadWriteProtocol:
    """Get a user-scoped instance of AuthTokenRepository."""
    return cast("AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository(user=user))


def get_calendar_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CalendarRepositoryReadWriteProtocol:
    """Get a user-scoped instance of CalendarRepository."""
    return cast("CalendarRepositoryReadWriteProtocol", CalendarRepository(user=user))


def get_time_block_definition_ro_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> TimeBlockDefinitionRepositoryReadOnlyProtocol:
    """Get a user-scoped instance of TimeBlockDefinitionRepository (read-only)."""
    return cast(
        "TimeBlockDefinitionRepositoryReadOnlyProtocol",
        TimeBlockDefinitionRepository(user=user),
    )


async def get_calendar_repo_by_user_id(
    user_id: Annotated[UUID, Path()],
) -> CalendarRepositoryReadOnlyProtocol:
    """Get a user-scoped CalendarRepository using user_id from path (for webhooks)."""
    user_repo = UserRepository()
    try:
        user = await user_repo.get(user_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    return cast("CalendarRepositoryReadOnlyProtocol", CalendarRepository(user=user))
