"""
Repository dependency injection functions.

Each function returns a user-scoped repository instance, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated, cast

from fastapi import Depends

from lykke.application.repositories import TimeBlockDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import TimeBlockDefinitionRepository
from lykke.presentation.api.routers.dependencies.user import get_current_user


def get_time_block_definition_ro_repo(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> TimeBlockDefinitionRepositoryReadOnlyProtocol:
    """Get a user-scoped instance of TimeBlockDefinitionRepository (read-only)."""
    return cast(
        "TimeBlockDefinitionRepositoryReadOnlyProtocol",
        TimeBlockDefinitionRepository(user=user),
    )
