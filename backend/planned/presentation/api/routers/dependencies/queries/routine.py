"""Routine query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.routine import (
    GetRoutineHandler,
    ListRoutinesHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_get_routine_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetRoutineHandler:
    """Get a GetRoutineHandler instance."""
    return GetRoutineHandler(uow_factory)


def get_list_routines_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListRoutinesHandler:
    """Get a ListRoutinesHandler instance."""
    return ListRoutinesHandler(uow_factory)

