"""DayTemplate command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.day_template import (
    CreateDayTemplateHandler,
    DeleteDayTemplateHandler,
    UpdateDayTemplateHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_create_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateDayTemplateHandler:
    """Get a CreateDayTemplateHandler instance."""
    return CreateDayTemplateHandler(uow_factory)


def get_update_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateDayTemplateHandler:
    """Get an UpdateDayTemplateHandler instance."""
    return UpdateDayTemplateHandler(uow_factory)


def get_delete_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteDayTemplateHandler:
    """Get a DeleteDayTemplateHandler instance."""
    return DeleteDayTemplateHandler(uow_factory)

