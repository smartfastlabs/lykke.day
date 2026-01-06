"""Background task definitions using Taskiq."""

from typing import Annotated
from uuid import UUID

from loguru import logger
from planned.application.commands.calendar import SyncAllCalendarsHandler
from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from planned.infrastructure.gateways import GoogleCalendarGateway
from planned.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from planned.infrastructure.workers.config import broker
from taskiq_dependencies import Depends


def get_google_gateway() -> GoogleCalendarGatewayProtocol:
    """Get a GoogleCalendarGateway instance."""
    return GoogleCalendarGateway()


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    return SqlAlchemyReadOnlyRepositoryFactory()


def get_sync_all_calendars_handler(
    user_id: UUID,
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_gateway)
    ],
) -> SyncAllCalendarsHandler:
    """Get a SyncAllCalendarsHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    return SyncAllCalendarsHandler(ro_repos, uow_factory, user_id, google_gateway)


@broker.task
async def sync_calendar_task(
    user_id: UUID,
    sync_handler: Annotated[
        SyncAllCalendarsHandler, Depends(get_sync_all_calendars_handler)
    ],
) -> None:
    """Sync all calendar entries for a specific user.

    This is an event-triggered task - enqueued when user requests a sync.

    Args:
        user_id: The user ID to sync calendars for.
        sync_handler: Injected SyncAllCalendarsHandler.
    """
    logger.info(f"Starting calendar sync for user {user_id}")

    await sync_handler.sync_all_calendars()

    logger.info(f"Calendar sync completed for user {user_id}")
