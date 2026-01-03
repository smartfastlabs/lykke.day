"""TaskDefinition query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    ListTaskDefinitionsHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_get_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetTaskDefinitionHandler:
    """Get a GetTaskDefinitionHandler instance."""
    return GetTaskDefinitionHandler(uow_factory)


def get_list_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListTaskDefinitionsHandler:
    """Get a ListTaskDefinitionsHandler instance."""
    return ListTaskDefinitionsHandler(uow_factory)

