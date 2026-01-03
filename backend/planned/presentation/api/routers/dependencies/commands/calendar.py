"""Calendar command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    UpdateCalendarHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_create_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateCalendarHandler:
    """Get a CreateCalendarHandler instance."""
    return CreateCalendarHandler(uow_factory)


def get_update_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateCalendarHandler:
    """Get an UpdateCalendarHandler instance."""
    return UpdateCalendarHandler(uow_factory)


def get_delete_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteCalendarHandler:
    """Get a DeleteCalendarHandler instance."""
    return DeleteCalendarHandler(uow_factory)

