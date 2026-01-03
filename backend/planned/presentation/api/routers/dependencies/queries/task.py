"""Task query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.task import ListTasksHandler
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_list_tasks_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListTasksHandler:
    """Get a ListTasksHandler instance."""
    return ListTasksHandler(uow_factory)

