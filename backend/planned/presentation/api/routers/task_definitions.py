"""Router for TaskDefinition CRUD operations."""

from fastapi import APIRouter
from planned.infrastructure.data.default_task_definitions import (
    DEFAULT_TASK_DEFINITIONS,
)
from planned.infrastructure.repositories import TaskDefinitionRepository
from planned.presentation.api.routers.generic import create_crud_router
from planned.presentation.api.routers.generic.config import (
    CRUDOperations,
    EntityRouterConfig,
)

# Create a new router and add the /available route FIRST (before CRUD routes)
router = APIRouter()


@router.get("/available")
async def get_available_task_definitions() -> list[dict]:
    """Get the curated list of available task definitions that users can import.

    Returns:
        List of task definition dictionaries (without user_id)
    """
    return DEFAULT_TASK_DEFINITIONS


# Include the CRUD router AFTER the /available route is registered
crud_router = create_crud_router(
    EntityRouterConfig(
        entity_name="task-definitions",
        repo_class=TaskDefinitionRepository,
        repository_name="task_definitions",
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
router.include_router(crud_router)
