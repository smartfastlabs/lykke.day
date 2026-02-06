"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Path

from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.repositories import (
    CalendarRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
)
from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import (
    CalendarRepository,
    TimeBlockDefinitionRepository,
)
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.api.routers.dependencies.user import get_current_user


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
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(lambda: UnauthenticatedIdentityAccess())
    ],
) -> CalendarRepositoryReadOnlyProtocol:
    """Get a user-scoped CalendarRepository using user_id from path (for webhooks)."""
    try:
        user = await identity_access.get_user_by_id(user_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return cast("CalendarRepositoryReadOnlyProtocol", CalendarRepository(user=user))
