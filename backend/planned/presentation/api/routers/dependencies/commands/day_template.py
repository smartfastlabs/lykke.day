"""DayTemplate command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.day_template import (
    CreateDayTemplateHandler,
    DeleteDayTemplateHandler,
    UpdateDayTemplateHandler,
)
from planned.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateDayTemplateHandler:
    """Get a CreateDayTemplateHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateDayTemplateHandler(ro_repos, uow_factory, user.id)


def get_update_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateDayTemplateHandler:
    """Get an UpdateDayTemplateHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateDayTemplateHandler(ro_repos, uow_factory, user.id)


def get_delete_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteDayTemplateHandler:
    """Get a DeleteDayTemplateHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteDayTemplateHandler(ro_repos, uow_factory, user.id)

