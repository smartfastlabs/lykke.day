"""Calendar command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    UpdateCalendarHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateCalendarHandler:
    """Get a CreateCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateCalendarHandler(ro_repos, uow_factory, user.id)


def get_update_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateCalendarHandler:
    """Get an UpdateCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateCalendarHandler(ro_repos, uow_factory, user.id)


def get_delete_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteCalendarHandler:
    """Get a DeleteCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteCalendarHandler(ro_repos, uow_factory, user.id)
