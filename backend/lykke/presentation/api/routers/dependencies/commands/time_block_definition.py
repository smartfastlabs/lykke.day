"""Dependencies for time block definition command handlers."""

from typing import Annotated

from fastapi import Depends

from lykke.application.commands.time_block_definition import (
    CreateTimeBlockDefinitionHandler,
    DeleteTimeBlockDefinitionHandler,
    UpdateTimeBlockDefinitionHandler,
)
from lykke.application.unit_of_work import UnitOfWorkFactory

from ..user import get_uow_factory


def get_create_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> CreateTimeBlockDefinitionHandler:
    """Get CreateTimeBlockDefinitionHandler with injected dependencies."""
    return CreateTimeBlockDefinitionHandler(uow_factory=uow_factory)


def get_update_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> UpdateTimeBlockDefinitionHandler:
    """Get UpdateTimeBlockDefinitionHandler with injected dependencies."""
    return UpdateTimeBlockDefinitionHandler(uow_factory=uow_factory)


def get_delete_time_block_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> DeleteTimeBlockDefinitionHandler:
    """Get DeleteTimeBlockDefinitionHandler with injected dependencies."""
    return DeleteTimeBlockDefinitionHandler(uow_factory=uow_factory)

