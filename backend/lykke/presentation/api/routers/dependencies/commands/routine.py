"""Routine command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.routine import (
    AddRoutineTaskHandler,
    CreateRoutineHandler,
    DeleteRoutineHandler,
    RemoveRoutineTaskHandler,
    UpdateRoutineHandler,
    UpdateRoutineTaskHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_routine_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateRoutineHandler:
    """Get a CreateRoutineHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateRoutineHandler(ro_repos, uow_factory, user.id)


def get_update_routine_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateRoutineHandler:
    """Get an UpdateRoutineHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateRoutineHandler(ro_repos, uow_factory, user.id)


def get_delete_routine_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteRoutineHandler:
    """Get a DeleteRoutineHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteRoutineHandler(ro_repos, uow_factory, user.id)


def get_add_routine_task_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AddRoutineTaskHandler:
    """Get an AddRoutineTaskHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return AddRoutineTaskHandler(ro_repos, uow_factory, user.id)


def get_update_routine_task_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateRoutineTaskHandler:
    """Get an UpdateRoutineTaskHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateRoutineTaskHandler(ro_repos, uow_factory, user.id)


def get_remove_routine_task_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RemoveRoutineTaskHandler:
    """Get a RemoveRoutineTaskHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return RemoveRoutineTaskHandler(ro_repos, uow_factory, user.id)


