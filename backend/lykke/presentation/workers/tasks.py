"""Background task definitions using Taskiq."""

from typing import Annotated, cast
from uuid import UUID

from loguru import logger
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_dependencies import Depends

from lykke.application.commands import ScheduleDayCommand, ScheduleDayHandler
from lykke.application.commands.calendar import (
    SubscribeCalendarCommand,
    SubscribeCalendarHandler,
    SyncAllCalendarsCommand,
    SyncAllCalendarsHandler,
    SyncCalendarCommand,
    SyncCalendarHandler,
)
from lykke.application.commands.notifications import (
    MorningOverviewCommand,
    MorningOverviewHandler,
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.events import register_all_handlers
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.queries import (
    ComputeTaskRiskHandler,
    GenerateUseCasePromptHandler,
    GetDayContextHandler,
    GetLLMPromptContextHandler,
    PreviewDayHandler,
)
from lykke.application.repositories import (
    PushNotificationRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.utils.dates import (
    get_current_date,
    get_current_datetime_in_timezone,
    get_current_time,
    resolve_timezone,
)
from lykke.domain import value_objects
from lykke.infrastructure.gateways import (
    GoogleCalendarGateway,
    RedisPubSubGateway,
    WebPushGateway,
)
from lykke.infrastructure.repositories import UserRepository
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.infrastructure.workers.config import broker

# Create a scheduler for periodic tasks
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])


def register_worker_event_handlers() -> None:
    """Register domain event handlers for background workers.

    Workers execute commands that emit domain events (e.g., calendar sync).
    Without registration, handlers like push notifications never run.
    """
    ro_repo_factory = get_read_only_repository_factory()
    uow_factory = get_unit_of_work_factory()
    register_all_handlers(ro_repo_factory=ro_repo_factory, uow_factory=uow_factory)
    logger.info("Registered domain event handlers for worker process")


def get_google_gateway() -> GoogleCalendarGatewayProtocol:
    """Get a GoogleCalendarGateway instance."""
    return GoogleCalendarGateway()


def get_unit_of_work_factory(
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance.

    Args:
        pubsub_gateway: Optional RedisPubSubGateway instance. If not provided,
            a new one will be created that connects lazily to Redis.
    """
    gateway = pubsub_gateway or RedisPubSubGateway()
    return SqlAlchemyUnitOfWorkFactory(pubsub_gateway=gateway)


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
    sync_calendar_handler = SyncCalendarHandler(
        ro_repos, uow_factory, user_id, google_gateway
    )
    return SyncAllCalendarsHandler(
        ro_repos, uow_factory, user_id, sync_calendar_handler
    )


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


def get_smart_notification_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> SmartNotificationHandler:
    """Get a SmartNotificationHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    get_day_context_handler = GetDayContextHandler(ro_repos, user_id)
    get_prompt_context_handler = GetLLMPromptContextHandler(
        ro_repos, user_id, get_day_context_handler
    )
    prompt_handler = GenerateUseCasePromptHandler(ro_repos, user_id)
    web_push_gateway = WebPushGateway()
    send_push_notification_handler = SendPushNotificationHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user_id,
        web_push_gateway=web_push_gateway,
    )
    return SmartNotificationHandler(
        ro_repos,
        uow_factory,
        user_id,
        get_prompt_context_handler,
        prompt_handler,
        send_push_notification_handler,
    )


def get_morning_overview_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> MorningOverviewHandler:
    """Get a MorningOverviewHandler instance for a user."""
    ro_repos = ro_repo_factory.create(user_id)
    get_day_context_handler = GetDayContextHandler(ro_repos, user_id)
    get_prompt_context_handler = GetLLMPromptContextHandler(
        ro_repos, user_id, get_day_context_handler
    )
    compute_task_risk_handler = ComputeTaskRiskHandler(ro_repos, user_id)
    prompt_handler = GenerateUseCasePromptHandler(ro_repos, user_id)
    web_push_gateway = WebPushGateway()
    send_push_notification_handler = SendPushNotificationHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user_id,
        web_push_gateway=web_push_gateway,
    )
    return MorningOverviewHandler(
        ro_repos,
        uow_factory,
        user_id,
        get_prompt_context_handler,
        compute_task_risk_handler,
        prompt_handler,
        send_push_notification_handler,
    )


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

    pubsub_gateway = RedisPubSubGateway()
    try:
        sync_handler = get_sync_all_calendars_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
            google_gateway=get_google_gateway(),
        )

        await sync_handler.handle(SyncAllCalendarsCommand())

        logger.info(f"Calendar sync completed for user {user_id}")
    finally:
        await pubsub_gateway.close()


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

    pubsub_gateway = RedisPubSubGateway()
    try:
        sync_handler = get_sync_calendar_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
            google_gateway=get_google_gateway(),
        )

        await sync_handler.handle(SyncCalendarCommand(calendar_id=calendar_id))

        logger.info(
            f"Single calendar sync completed for user {user_id}, calendar {calendar_id}"
        )
    finally:
        await pubsub_gateway.close()


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

    pubsub_gateway = RedisPubSubGateway()
    try:
        subscribe_handler = get_subscribe_calendar_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
            google_gateway=get_google_gateway(),
        )

        ro_repos = get_read_only_repository_factory().create(user_id)
        calendar = await ro_repos.calendar_ro_repo.get(calendar_id)

        await subscribe_handler.handle(SubscribeCalendarCommand(calendar=calendar))

        logger.info(
            f"Calendar resubscription completed for user {user_id}, calendar {calendar_id}"
        )
    finally:
        await pubsub_gateway.close()


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
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Schedule today's day for a specific user."""
    logger.info(f"Starting daily scheduling for user {user_id}")

    pubsub_gateway = RedisPubSubGateway()
    try:
        schedule_handler = get_schedule_day_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            user = await user_repo.get(user_id)
            timezone = user.settings.timezone if user.settings else None
        except Exception:
            timezone = None

        # Use user's timezone for "today"
        target_date = get_current_date(timezone)
        try:
            await schedule_handler.handle(ScheduleDayCommand(date=target_date))
            logger.debug(f"Scheduled {target_date} for user {user_id}")
        except ValueError as e:
            # Day template might be missing - log and continue
            logger.warning(f"Could not schedule {target_date} for user {user_id}: {e}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job - continue with other users
            logger.exception(f"Error scheduling {target_date} for user {user_id}")

        logger.info(f"Daily scheduling completed for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task(schedule=[{"cron": "0,20,30,50 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_smart_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate smart notifications for all users with LLM provider configured.

    Runs at :00, :20, :30, and :50 each hour to check notifications.
    """
    logger.info("Starting smart notification evaluation for all users")

    users = await user_repo.all()
    # Filter to users with LLM provider configured
    users_with_llm = [
        user for user in users if user.settings and user.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")

    for user in users_with_llm:
        # Enqueue a sub-task for each user
        await evaluate_smart_notification_task.kiq(
            user_id=user.id, triggered_by="scheduled"
        )

    logger.info(
        f"Enqueued smart notification evaluation tasks for {len(users_with_llm)} users"
    )


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_smart_notification_task(
    user_id: UUID,
    triggered_by: str | None = None,
) -> None:
    """Evaluate and send smart notification for a specific user.

    This task can be triggered by:
    - Scheduled task (every 10 minutes)
    - Domain events (task status changes)

    Args:
        user_id: The user ID to evaluate notifications for
        triggered_by: How this task was triggered (e.g., "scheduled", "task_status_change")
    """
    logger.info(f"Starting smart notification evaluation for user {user_id}")

    pubsub_gateway = RedisPubSubGateway()
    try:
        handler = get_smart_notification_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            await handler.handle(
                SmartNotificationCommand(
                    user_id=user_id,
                    triggered_by=triggered_by,
                )
            )
            logger.debug(f"Smart notification evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job - continue with other users
            logger.exception(f"Error evaluating smart notification for user {user_id}")

    finally:
        await pubsub_gateway.close()


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


@broker.task(schedule=[{"cron": "*/15 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_morning_overviews_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate morning overviews for all users with configured overview time.

    Runs every 15 minutes to check which users should receive their morning overview.
    Only sends once per day per user.
    """
    logger.info("Starting morning overview evaluation for all users")

    users = await user_repo.all()
    # Filter to users with LLM provider and morning overview time configured
    eligible_users = [
        user
        for user in users
        if user.settings
        and user.settings.llm_provider
        and user.settings.morning_overview_time
    ]
    logger.info(f"Found {len(eligible_users)} users eligible for morning overview")

    ro_repo_factory = get_read_only_repository_factory()

    for user in eligible_users:
        try:
            # Parse the morning overview time (HH:MM format)
            overview_time_str = user.settings.morning_overview_time
            if not overview_time_str:
                continue

            try:
                hour_str, minute_str = overview_time_str.split(":")
                overview_hour = int(hour_str)
                overview_minute = int(minute_str)
            except (ValueError, AttributeError):
                logger.warning(
                    f"Invalid morning_overview_time format for user {user.id}: {overview_time_str}"
                )
                continue

            # Get current time in user's timezone
            current_time = get_current_time(user.settings.timezone)
            current_hour = current_time.hour
            current_minute = current_time.minute

            # Check if current time matches overview time (within 15 minute window)
            # We check if we're within 0-14 minutes past the target time
            time_matches = (
                current_hour == overview_hour
                and current_minute >= overview_minute
                and current_minute < overview_minute + 15
            )

            if not time_matches:
                continue

            # Check if we've already sent today
            ro_repos = ro_repo_factory.create(user.id)
            push_notification_repo: PushNotificationRepositoryReadOnlyProtocol = (
                ro_repos.push_notification_ro_repo
            )

            today = get_current_date(user.settings.timezone)
            today_start = get_current_datetime_in_timezone(user.settings.timezone)
            today_start = today_start.replace(hour=0, minute=0, second=0, microsecond=0)

            # Check for morning overview notifications sent today
            existing_notifications = await push_notification_repo.search(
                value_objects.PushNotificationQuery(
                    sent_after=today_start,
                    status="sent",
                )
            )

            # Filter to morning overview notifications
            morning_overview_sent_today = any(
                n.triggered_by == "morning_overview" for n in existing_notifications
            )

            if morning_overview_sent_today:
                logger.debug(
                    f"Morning overview already sent today for user {user.id}, skipping"
                )
                continue

            # Enqueue the morning overview task
            await evaluate_morning_overview_task.kiq(user_id=user.id)
            logger.info(f"Enqueued morning overview for user {user.id}")

        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error checking morning overview for user {user.id}")

    logger.info("Completed morning overview evaluation for all users")


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_morning_overview_task(
    user_id: UUID,
) -> None:
    """Evaluate and send morning overview for a specific user.

    Args:
        user_id: The user ID to send morning overview for
    """
    logger.info(f"Starting morning overview evaluation for user {user_id}")

    pubsub_gateway = RedisPubSubGateway()
    try:
        handler = get_morning_overview_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            await handler.handle(MorningOverviewCommand(user_id=user_id))
            logger.debug(f"Morning overview evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job
            logger.exception(f"Error evaluating morning overview for user {user_id}")

    finally:
        await pubsub_gateway.close()


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


# Ensure handlers are registered when the worker tasks module is imported
register_worker_event_handlers()
