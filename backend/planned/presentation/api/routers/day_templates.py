"""Router for DayTemplate CRUD operations."""

from planned.infrastructure.repositories import DayTemplateRepository
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
        repo_loader=get_day_template_repo,
        repo_class=DayTemplateRepository,
        operations=CRUDOperations(
            enable_get=True,
            enable_list=True,
            enable_create=True,
            enable_update=True,
            enable_delete=True,
        ),
        tags=["day-templates"],
    )
)

