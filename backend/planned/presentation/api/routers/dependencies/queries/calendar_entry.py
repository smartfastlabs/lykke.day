"""CalendarEntry query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.calendar_entry import ListCalendarEntriesHandler
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_list_calendar_entries_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListCalendarEntriesHandler:
    """Get a ListCalendarEntriesHandler instance."""
    return ListCalendarEntriesHandler(uow_factory)

