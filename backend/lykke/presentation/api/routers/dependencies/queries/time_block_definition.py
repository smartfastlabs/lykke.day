"""Dependencies for time block definition query handlers."""

from typing import Annotated

from fastapi import Depends

from lykke.application.queries.time_block_definition import (
    GetTimeBlockDefinitionHandler,
    SearchTimeBlockDefinitionsHandler,
)
from lykke.application.repositories import ReadOnlyRepositoryFactory

from ..user import get_ro_repo_factory


def get_get_time_block_definition_handler(
    ro_repo_factory: Annotated[ReadOnlyRepositoryFactory, Depends(get_ro_repo_factory)],
) -> GetTimeBlockDefinitionHandler:
    """Get GetTimeBlockDefinitionHandler with injected dependencies."""
    return GetTimeBlockDefinitionHandler(ro_repo_factory=ro_repo_factory)


def get_list_time_block_definitions_handler(
    ro_repo_factory: Annotated[ReadOnlyRepositoryFactory, Depends(get_ro_repo_factory)],
) -> SearchTimeBlockDefinitionsHandler:
    """Get SearchTimeBlockDefinitionsHandler with injected dependencies."""
    return SearchTimeBlockDefinitionsHandler(ro_repo_factory=ro_repo_factory)

