"""User command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.user import UpdateUserHandler
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_update_user_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateUserHandler:
    """Get an UpdateUserHandler instance."""
    return UpdateUserHandler(uow_factory)

