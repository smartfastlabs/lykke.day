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
from planned.domain.entities import UserEntity

from ..services import get_unit_of_work_factory
from ..user import get_current_user


def get_create_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateTaskDefinitionHandler:
    """Get a CreateTaskDefinitionHandler instance."""
    return CreateTaskDefinitionHandler(uow_factory, user.id)


def get_update_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateTaskDefinitionHandler:
    """Get an UpdateTaskDefinitionHandler instance."""
    return UpdateTaskDefinitionHandler(uow_factory, user.id)


def get_delete_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteTaskDefinitionHandler:
    """Get a DeleteTaskDefinitionHandler instance."""
    return DeleteTaskDefinitionHandler(uow_factory, user.id)


def get_bulk_create_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BulkCreateTaskDefinitionsHandler:
    """Get a BulkCreateTaskDefinitionsHandler instance."""
    return BulkCreateTaskDefinitionsHandler(uow_factory, user.id)

