"""Background task definitions using Taskiq."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, cast
from uuid import UUID

from loguru import logger
from lykke.application.commands import ScheduleDayHandler
from lykke.application.commands.calendar import SyncAllCalendarsHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.queries import PreviewDayHandler
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from lykke.infrastructure.gateways import GoogleCalendarGateway
from lykke.infrastructure.repositories import UserRepository
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.infrastructure.workers.config import broker
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_dependencies import Depends

# Create a scheduler for periodic tasks
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])


def get_google_gateway() -> GoogleCalendarGatewayProtocol:
    """Get a GoogleCalendarGateway instance."""
    return GoogleCalendarGateway()


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    return SqlAlchemyReadOnlyRepositoryFactory()


def get_user_repository() -> UserRepositoryReadOnlyProtocol:
    """Get a UserRepository instance (not user-scoped)."""
    return cast("UserRepositoryReadOnlyProtocol", UserRepository())


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


def get_schedule_day_handler(
    user_id: UUID,
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    preview_day_handler = PreviewDayHandler(ro_repos, user_id)
    return ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_day_handler)


@broker.task  # type: ignore[untyped-decorator]
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


@broker.task  # type: ignore[untyped-decorator]
async def schedule_all_users_week_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Load all users and enqueue scheduling tasks for each user.

    This is the parent task that fans out to per-user scheduling tasks.
    It is one of the few tasks that is NOT scoped to a specific user.
    """
    logger.info("Starting scheduled week task for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to schedule")

    for user in users:
        # Enqueue a sub-task for each user
        await schedule_user_week_task.kiq(user_id=user.id)

    logger.info(f"Enqueued scheduling tasks for {len(users)} users")


@broker.task  # type: ignore[untyped-decorator]
async def schedule_user_week_task(
    user_id: UUID,
    schedule_handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> None:
    """Schedule all days for the next week for a specific user.

    Args:
        user_id: The user ID to schedule days for.
        schedule_handler: Injected ScheduleDayHandler.
    """
    logger.info(f"Starting week scheduling for user {user_id}")

    today = datetime.now(UTC).date()
    days_scheduled = 0

    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset)
        try:
            await schedule_handler.schedule_day(date=target_date)
            days_scheduled += 1
            logger.debug(f"Scheduled {target_date} for user {user_id}")
        except ValueError as e:
            # Day template might be missing for some days - log and continue
            logger.warning(f"Could not schedule {target_date} for user {user_id}: {e}")
        except Exception:
            # Catch-all for resilient background job - continue with other days
            logger.exception(f"Error scheduling {target_date} for user {user_id}")

    logger.info(
        f"Week scheduling completed for user {user_id}: {days_scheduled}/7 days scheduled"
    )


# =============================================================================
# Example Tasks
# =============================================================================


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def heartbeat_task() -> None:
    """Heartbeat task that runs every minute.

    This is a simple example of a scheduled task that logs a message.
    Useful for verifying that the worker is running and processing tasks.
    """
    logger.info("💓 Heartbeat: Worker is alive and processing tasks")


@broker.task  # type: ignore[untyped-decorator]
async def example_triggered_task(message: str) -> dict[str, str]:
    """Example task that can be triggered via API.

    This demonstrates a task that can be enqueued on-demand from an API endpoint.

    Args:
        message: A message to include in the task output.

    Returns:
        A dictionary with the task result.
    """
    logger.info(f"Example triggered task received message: {message}")
    return {"status": "completed", "message": message}
