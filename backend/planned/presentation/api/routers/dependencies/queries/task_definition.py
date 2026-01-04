"""TaskDefinition query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    ListTaskDefinitionsHandler,
)
from planned.application.unit_of_work import ReadOnlyRepositoryFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_get_task_definition_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetTaskDefinitionHandler:
    """Get a GetTaskDefinitionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetTaskDefinitionHandler(ro_repos, user.id)


def get_list_task_definitions_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> ListTaskDefinitionsHandler:
    """Get a ListTaskDefinitionsHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ListTaskDefinitionsHandler(ro_repos, user.id)

