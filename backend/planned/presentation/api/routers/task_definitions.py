"""Router for TaskDefinition CRUD operations."""

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
        ),
        tags=["task-definitions"],
    )
)

