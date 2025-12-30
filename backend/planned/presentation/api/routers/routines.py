"""Router for Routine CRUD operations."""

from planned.infrastructure.repositories import RoutineRepository
from planned.presentation.api.routers.dependencies.repositories import (
    get_routine_repo,
)
from planned.presentation.api.routers.generic import create_crud_router
from planned.presentation.api.routers.generic.config import (
    CRUDOperations,
    EntityRouterConfig,
)

router = create_crud_router(
    EntityRouterConfig(
        entity_name="routines",
        repo_loader=get_routine_repo,
        repo_class=RoutineRepository,
        operations=CRUDOperations(
            enable_get=True,
            enable_list=True,
            enable_create=False,
            enable_update=False,
            enable_delete=False,
        ),
        tags=["routines"],
    )
)

