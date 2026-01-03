"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated

from fastapi import Depends
from planned.application.commands import (
    RecordTaskActionHandler,
    ScheduleDayHandler,
    UpdateDayHandler,
)
from planned.application.queries import GetDayContextHandler, PreviewDayHandler
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory

from ..user import get_current_user


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


# Query Handler Dependencies
def get_get_day_context_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetDayContextHandler:
    """Get a GetDayContextHandler instance."""
    return GetDayContextHandler(uow_factory)


def get_preview_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> PreviewDayHandler:
    """Get a PreviewDayHandler instance."""
    return PreviewDayHandler(uow_factory)


# Command Handler Dependencies
def get_schedule_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance."""
    return ScheduleDayHandler(uow_factory)


def get_update_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateDayHandler:
    """Get an UpdateDayHandler instance."""
    return UpdateDayHandler(uow_factory)


def get_record_task_action_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> RecordTaskActionHandler:
    """Get a RecordTaskActionHandler instance."""
    return RecordTaskActionHandler(uow_factory)
