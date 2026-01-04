"""Calendar command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    UpdateCalendarHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import UserEntity

from ..services import get_unit_of_work_factory
from ..user import get_current_user


def get_create_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateCalendarHandler:
    """Get a CreateCalendarHandler instance."""
    return CreateCalendarHandler(uow_factory, user.id)


def get_update_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateCalendarHandler:
    """Get an UpdateCalendarHandler instance."""
    return UpdateCalendarHandler(uow_factory, user.id)


def get_delete_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteCalendarHandler:
    """Get a DeleteCalendarHandler instance."""
    return DeleteCalendarHandler(uow_factory, user.id)

