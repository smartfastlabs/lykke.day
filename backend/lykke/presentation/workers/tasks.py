"""Background task definitions using Taskiq."""

from typing import Annotated, cast
from uuid import UUID

from loguru import logger
from lykke.application.commands import ScheduleDayHandler
from lykke.application.commands.calendar import (
    SubscribeCalendarHandler,
    SyncAllCalendarsHandler,
    SyncCalendarHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.queries import PreviewDayHandler
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.utils.dates import get_current_date
from lykke.infrastructure.gateways import GoogleCalendarGateway, StubPubSubGateway
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
    """Get a UnitOfWorkFactory instance.
    
    Uses StubPubSubGateway since background workers don't need to broadcast events.
    """
    return SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    return SqlAlchemyReadOnlyRepositoryFactory()


def get_user_repository() -> UserRepositoryReadOnlyProtocol:
    """Get a UserRepository instance (not user-scoped)."""
    return cast("UserRepositoryReadOnlyProtocol", UserRepository())


def get_sync_all_calendars_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SyncAllCalendarsHandler:
    """Get a SyncAllCalendarsHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    return SyncAllCalendarsHandler(ro_repos, uow_factory, user_id, google_gateway)


def get_sync_calendar_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SyncCalendarHandler:
    """Get a SyncCalendarHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    return SyncCalendarHandler(ro_repos, uow_factory, user_id, google_gateway)


def get_subscribe_calendar_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SubscribeCalendarHandler:
    """Get a SubscribeCalendarHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    return SubscribeCalendarHandler(ro_repos, uow_factory, user_id, google_gateway)


def get_schedule_day_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    preview_day_handler = PreviewDayHandler(ro_repos, user_id)
    return ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_day_handler)


@broker.task  # type: ignore[untyped-decorator]
async def sync_calendar_task(
    user_id: UUID,
) -> None:
    """Sync all calendar entries for a specific user.

    This is an event-triggered task - enqueued when user requests a sync.

    Args:
        user_id: The user ID to sync calendars for.
    """
    logger.info(f"Starting calendar sync for user {user_id}")

    sync_handler = get_sync_all_calendars_handler(
        user_id=user_id,
        uow_factory=get_unit_of_work_factory(),
        ro_repo_factory=get_read_only_repository_factory(),
        google_gateway=get_google_gateway(),
    )

    await sync_handler.sync_all_calendars()

    logger.info(f"Calendar sync completed for user {user_id}")


@broker.task  # type: ignore[untyped-decorator]
async def sync_single_calendar_task(
    user_id: UUID,
    calendar_id: UUID,
) -> None:
    """Sync a single calendar for a user (triggered by webhook).

    This task is enqueued when a Google Calendar webhook notification is received.

    Args:
        user_id: The user ID that owns the calendar.
        calendar_id: The calendar ID to sync.
    """
    logger.info(
        f"Starting single calendar sync for user {user_id}, calendar {calendar_id}"
    )

    sync_handler = get_sync_calendar_handler(
        user_id=user_id,
        uow_factory=get_unit_of_work_factory(),
        ro_repo_factory=get_read_only_repository_factory(),
        google_gateway=get_google_gateway(),
    )

    await sync_handler.sync_calendar(calendar_id)

    logger.info(
        f"Single calendar sync completed for user {user_id}, calendar {calendar_id}"
    )


@broker.task  # type: ignore[untyped-decorator]
async def resubscribe_calendar_task(
    user_id: UUID,
    calendar_id: UUID,
) -> None:
    """Resubscribe a calendar to push notifications (after re-authentication).

    This task is enqueued after re-authentication to recreate subscriptions
    with new credentials. The old subscriptions are left as orphans in Google.

    Args:
        user_id: The user ID that owns the calendar.
        calendar_id: The calendar ID to resubscribe.
    """
    logger.info(
        f"Starting calendar resubscription for user {user_id}, calendar {calendar_id}"
    )

    subscribe_handler = get_subscribe_calendar_handler(
        user_id=user_id,
        uow_factory=get_unit_of_work_factory(),
        ro_repo_factory=get_read_only_repository_factory(),
        google_gateway=get_google_gateway(),
    )

    ro_repos = get_read_only_repository_factory().create(user_id)
    calendar = await ro_repos.calendar_ro_repo.get(calendar_id)

    await subscribe_handler.subscribe(calendar)

    logger.info(
        f"Calendar resubscription completed for user {user_id}, calendar {calendar_id}"
    )


@broker.task(schedule=[{"cron": "0 3 * * *"}])  # type: ignore[untyped-decorator]
async def schedule_all_users_day_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Load all users and enqueue daily scheduling tasks for each user."""
    logger.info("Starting daily schedule task for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to schedule")

    for user in users:
        # Enqueue a sub-task for each user
        await schedule_user_day_task.kiq(user_id=user.id)

    logger.info(f"Enqueued daily scheduling tasks for {len(users)} users")


@broker.task  # type: ignore[untyped-decorator]
async def schedule_user_day_task(
    user_id: UUID,
) -> None:
    """Schedule today's day for a specific user."""
    logger.info(f"Starting daily scheduling for user {user_id}")

    schedule_handler = get_schedule_day_handler(
        user_id=user_id,
        uow_factory=get_unit_of_work_factory(),
        ro_repo_factory=get_read_only_repository_factory(),
    )

    # Uses the configured timezone for "today"
    target_date = get_current_date()
    try:
        await schedule_handler.schedule_day(date=target_date)
        logger.debug(f"Scheduled {target_date} for user {user_id}")
    except ValueError as e:
        # Day template might be missing - log and continue
        logger.warning(f"Could not schedule {target_date} for user {user_id}: {e}")
    except Exception:  # pylint: disable=broad-except
        # Catch-all for resilient background job - continue with other users
        logger.exception(f"Error scheduling {target_date} for user {user_id}")

    logger.info(f"Daily scheduling completed for user {user_id}")


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
