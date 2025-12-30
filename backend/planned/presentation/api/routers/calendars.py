"""Router for Calendar CRUD operations."""

from planned.infrastructure.repositories import CalendarRepository
from planned.presentation.api.routers.dependencies.repositories import (
    get_calendar_repo,
)
from planned.presentation.api.routers.generic import create_crud_router
from planned.presentation.api.routers.generic.config import (
    CRUDOperations,
    EntityRouterConfig,
)

router = create_crud_router(
    EntityRouterConfig(
        entity_name="calendars",
        repo_loader=get_calendar_repo,
        repo_class=CalendarRepository,
        operations=CRUDOperations(
            enable_get=True,
            enable_list=True,
            enable_create=True,
            enable_update=True,
            enable_delete=True,
        ),
        tags=["calendars"],
    )
)

