"""TaskDefinition command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.task_definition import (
    BulkCreateTaskDefinitionsHandler,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateTaskDefinitionHandler:
    """Get a CreateTaskDefinitionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateTaskDefinitionHandler(ro_repos, uow_factory, user.id)


def get_update_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateTaskDefinitionHandler:
    """Get an UpdateTaskDefinitionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateTaskDefinitionHandler(ro_repos, uow_factory, user.id)


def get_delete_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteTaskDefinitionHandler:
    """Get a DeleteTaskDefinitionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteTaskDefinitionHandler(ro_repos, uow_factory, user.id)


def get_bulk_create_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BulkCreateTaskDefinitionsHandler:
    """Get a BulkCreateTaskDefinitionsHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return BulkCreateTaskDefinitionsHandler(ro_repos, uow_factory, user.id)

