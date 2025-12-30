"""Router for DayTemplate CRUD operations."""

from planned.presentation.api.routers.dependencies.repositories import (
    get_day_template_repo,
)
from planned.presentation.api.routers.generic import create_crud_router
from planned.presentation.api.routers.generic.config import (
    CRUDOperations,
    EntityRouterConfig,
)

router = create_crud_router(
    EntityRouterConfig(
        entity_name="day-templates",
        repository_dependency=get_day_template_repo,
        operations=CRUDOperations(
            enable_get=True,
            enable_list=True,
            enable_create=True,  # via PUT
            enable_update=True,  # via PUT
            enable_delete=True,
        ),
        tags=["day-templates"],
    )
)

