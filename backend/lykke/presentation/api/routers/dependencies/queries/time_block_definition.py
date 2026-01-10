"""Dependencies for time block definition query handlers."""

from typing import Annotated

from fastapi import Depends

from lykke.application.queries.time_block_definition import (
    GetTimeBlockDefinitionHandler,
    SearchTimeBlockDefinitionsHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_get_time_block_definition_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetTimeBlockDefinitionHandler:
    """Get GetTimeBlockDefinitionHandler with injected dependencies."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetTimeBlockDefinitionHandler(ro_repos, user.id)


def get_list_time_block_definitions_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SearchTimeBlockDefinitionsHandler:
    """Get SearchTimeBlockDefinitionsHandler with injected dependencies."""
    ro_repos = ro_repo_factory.create(user.id)
    return SearchTimeBlockDefinitionsHandler(ro_repos, user.id)

