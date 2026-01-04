"""Routine query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.routine import (
    GetRoutineHandler,
    ListRoutinesHandler,
)
from planned.application.unit_of_work import ReadOnlyRepositoryFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_get_routine_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetRoutineHandler:
    """Get a GetRoutineHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetRoutineHandler(ro_repos, user.id)


def get_list_routines_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> ListRoutinesHandler:
    """Get a ListRoutinesHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ListRoutinesHandler(ro_repos, user.id)

