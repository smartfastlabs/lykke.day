"""Calendar query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.calendar import (
    GetCalendarHandler,
    ListCalendarsHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_get_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetCalendarHandler:
    """Get a GetCalendarHandler instance."""
    return GetCalendarHandler(uow_factory)


def get_list_calendars_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListCalendarsHandler:
    """Get a ListCalendarsHandler instance."""
    return ListCalendarsHandler(uow_factory)

