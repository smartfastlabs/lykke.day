"""TaskDefinition command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.task_definition import (
    BulkCreateTaskDefinitionsHandler,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_create_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateTaskDefinitionHandler:
    """Get a CreateTaskDefinitionHandler instance."""
    return CreateTaskDefinitionHandler(uow_factory)


def get_update_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateTaskDefinitionHandler:
    """Get an UpdateTaskDefinitionHandler instance."""
    return UpdateTaskDefinitionHandler(uow_factory)


def get_delete_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteTaskDefinitionHandler:
    """Get a DeleteTaskDefinitionHandler instance."""
    return DeleteTaskDefinitionHandler(uow_factory)


def get_bulk_create_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> BulkCreateTaskDefinitionsHandler:
    """Get a BulkCreateTaskDefinitionsHandler instance."""
    return BulkCreateTaskDefinitionsHandler(uow_factory)

