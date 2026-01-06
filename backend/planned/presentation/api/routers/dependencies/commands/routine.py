"""Routine command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.routine import (
    CreateRoutineHandler,
    DeleteRoutineHandler,
    UpdateRoutineHandler,
)
from planned.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from planned.domain.entities import UserEntity

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


