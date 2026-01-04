"""User command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.user import UpdateUserHandler
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import UserEntity

from ..services import get_unit_of_work_factory
from ..user import get_current_user


def get_update_user_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateUserHandler:
    """Get an UpdateUserHandler instance."""
    return UpdateUserHandler(uow_factory, user.id)

