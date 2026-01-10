"""Dependencies for time block definition command handlers."""

from typing import Annotated

from fastapi import Depends

from lykke.application.commands.time_block_definition import (
    CreateTimeBlockDefinitionHandler,
    DeleteTimeBlockDefinitionHandler,
    UpdateTimeBlockDefinitionHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateTimeBlockDefinitionHandler:
    """Get CreateTimeBlockDefinitionHandler with injected dependencies."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateTimeBlockDefinitionHandler(ro_repos, uow_factory, user.id)


def get_update_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateTimeBlockDefinitionHandler:
    """Get UpdateTimeBlockDefinitionHandler with injected dependencies."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateTimeBlockDefinitionHandler(ro_repos, uow_factory, user.id)


def get_delete_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteTimeBlockDefinitionHandler:
    """Get DeleteTimeBlockDefinitionHandler with injected dependencies."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteTimeBlockDefinitionHandler(ro_repos, uow_factory, user.id)

