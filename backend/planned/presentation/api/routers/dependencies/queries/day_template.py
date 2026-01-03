"""DayTemplate query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.day_template import (
    GetDayTemplateHandler,
    ListDayTemplatesHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_get_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetDayTemplateHandler:
    """Get a GetDayTemplateHandler instance."""
    return GetDayTemplateHandler(uow_factory)


def get_list_day_templates_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListDayTemplatesHandler:
    """Get a ListDayTemplatesHandler instance."""
    return ListDayTemplatesHandler(uow_factory)

