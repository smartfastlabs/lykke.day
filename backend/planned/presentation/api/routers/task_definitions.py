"""Router for TaskDefinition CRUD operations."""

from fastapi import APIRouter

from planned.infrastructure.data.default_task_definitions import DEFAULT_TASK_DEFINITIONS
from planned.infrastructure.repositories import TaskDefinitionRepository
from planned.presentation.api.routers.dependencies.repositories import (
    get_task_definition_repo,
)
from planned.presentation.api.routers.generic import create_crud_router
from planned.presentation.api.routers.generic.config import (
    CRUDOperations,
    EntityRouterConfig,
)

router = create_crud_router(
    EntityRouterConfig(
        entity_name="task-definitions",
        repo_loader=get_task_definition_repo,
        repo_class=TaskDefinitionRepository,
        operations=CRUDOperations(
            enable_get=True,
            enable_list=True,
            enable_create=True,
            enable_update=True,
            enable_delete=True,
            enable_bulk_create=True,
        ),
        tags=["task-definitions"],
    )
)


@router.get("/available")
async def get_available_task_definitions() -> list[dict]:
    """Get the curated list of available task definitions that users can import.
    
    Returns:
        List of task definition dictionaries (without user_id)
    """
    return DEFAULT_TASK_DEFINITIONS

