"""Background task definitions using Taskiq."""

from datetime import date as dt_date, timedelta as dt_timedelta
from typing import Annotated, cast
from uuid import UUID

from loguru import logger
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_dependencies import Depends

from lykke.application.commands import (
    EvaluateTimingStatusCommand,
    EvaluateTimingStatusHandler,
    ScheduleDayCommand,
    ScheduleDayHandler,
)
from lykke.application.commands.brain_dump import (
    ProcessBrainDumpCommand,
    ProcessBrainDumpHandler,
)
from lykke.application.commands.calendar import (
    SubscribeCalendarCommand,
    SubscribeCalendarHandler,
    SyncAllCalendarsCommand,
    SyncAllCalendarsHandler,
    SyncCalendarCommand,
    SyncCalendarHandler,
)
from lykke.application.commands.notifications import (
    KioskNotificationCommand,
    KioskNotificationHandler,
    MorningOverviewCommand,
    MorningOverviewHandler,
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from lykke.application.events import register_all_handlers
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import (
    PushNotificationRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.utils.dates import (
    get_current_date,
    get_current_datetime,
    get_current_datetime_in_timezone,
    get_current_time,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.infrastructure.gateways import GoogleCalendarGateway, RedisPubSubGateway
from lykke.infrastructure.repositories import UserRepository
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.infrastructure.workers.config import broker
from lykke.presentation.handler_factory import CommandHandlerFactory

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
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SyncAllCalendarsHandler)


def get_sync_calendar_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SyncCalendarHandler:
    """Get a SyncCalendarHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SyncCalendarHandler)


def get_subscribe_calendar_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SubscribeCalendarHandler:
    """Get a SubscribeCalendarHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SubscribeCalendarHandler)


def get_schedule_day_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ScheduleDayHandler)


def get_smart_notification_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> SmartNotificationHandler:
    """Get a SmartNotificationHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(SmartNotificationHandler)


def get_kiosk_notification_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> KioskNotificationHandler:
    """Get a KioskNotificationHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(KioskNotificationHandler)


def get_morning_overview_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> MorningOverviewHandler:
    """Get a MorningOverviewHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(MorningOverviewHandler)


def get_process_brain_dump_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ProcessBrainDumpHandler:
    """Get a ProcessBrainDumpHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ProcessBrainDumpHandler)


def get_evaluate_timing_status_handler(
    user_id: UUID,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> EvaluateTimingStatusHandler:
    """Get an EvaluateTimingStatusHandler instance for a user."""
    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(EvaluateTimingStatusHandler)


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

        target_date = get_current_date(timezone)
        try:
            await schedule_handler.handle(ScheduleDayCommand(date=target_date))
            logger.debug(f"Scheduled {target_date} for user {user_id}")
        except ValueError as e:
            logger.warning(f"Could not schedule {target_date} for user {user_id}: {e}")
        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error scheduling {target_date} for user {user_id}")

        logger.info(f"Daily scheduling completed for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task(schedule=[{"cron": "0,19,20,30,50 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_smart_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate smart notifications for all users with LLM provider configured.

    Runs at :00, :20, :30, and :50 each hour to check notifications.
    """
    logger.info("Starting smart notification evaluation for all users")

    users = await user_repo.all()
    users_with_llm = [
        user for user in users if user.settings and user.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")

    for user in users_with_llm:
        await evaluate_smart_notification_task.kiq(
            user_id=user.id, triggered_by="scheduled"
        )

    logger.info(
        f"Enqueued smart notification evaluation tasks for {len(users_with_llm)} users"
    )


@broker.task(schedule=[{"cron": "0,19,20,30,50 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_kiosk_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate kiosk notifications for all users with LLM provider configured.

    Runs at :00, :20, :30, and :50 each hour to check kiosk notifications.
    """
    logger.info("Starting kiosk notification evaluation for all users")

    users = await user_repo.all()
    users_with_llm = [
        user for user in users if user.settings and user.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")

    for user in users_with_llm:
        await evaluate_kiosk_notification_task.kiq(
            user_id=user.id, triggered_by="scheduled"
        )

    logger.info(
        f"Enqueued kiosk notification evaluation tasks for {len(users_with_llm)} users"
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
            logger.exception(f"Error evaluating smart notification for user {user_id}")

    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_kiosk_notification_task(
    user_id: UUID,
    triggered_by: str | None = None,
) -> None:
    """Evaluate and send kiosk notification for a specific user.

    This task can be triggered by:
    - Scheduled task (every 10 minutes)

    Args:
        user_id: The user ID to evaluate kiosk notifications for
        triggered_by: How this task was triggered (e.g., "scheduled")
    """
    logger.info(f"Starting kiosk notification evaluation for user {user_id}")

    pubsub_gateway = RedisPubSubGateway()
    try:
        handler = get_kiosk_notification_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            await handler.handle(
                KioskNotificationCommand(
                    user_id=user_id,
                    triggered_by=triggered_by,
                )
            )
            logger.debug(f"Kiosk notification evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error evaluating kiosk notification for user {user_id}")

    finally:
        await pubsub_gateway.close()


# =============================================================================
# Example Tasks
# =============================================================================


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def trigger_alarms_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Trigger alarms for all users every minute."""
    logger.info("Starting alarm trigger evaluation for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to evaluate alarms")

    for user in users:
        await trigger_alarms_for_user_task.kiq(user_id=user.id)

    logger.info("Enqueued alarm trigger tasks for all users")


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_timing_status_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate timing status changes for all users every minute."""
    logger.info("Starting timing status evaluation for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to evaluate timing status")

    for user in users:
        await evaluate_timing_status_for_user_task.kiq(user_id=user.id)

    logger.info("Enqueued timing status evaluation tasks for all users")


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_timing_status_for_user_task(
    user_id: UUID,
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate timing status changes for a specific user."""
    logger.info("Evaluating timing status for user %s", user_id)

    pubsub_gateway = RedisPubSubGateway()
    try:
        handler = get_evaluate_timing_status_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            await handler.handle(EvaluateTimingStatusCommand())
            logger.debug("Timing status evaluation completed for user %s", user_id)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error evaluating timing status for user %s", user_id)
    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def trigger_alarms_for_user_task(
    user_id: UUID,
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Trigger alarms for a specific user."""
    logger.info(f"Evaluating alarms for user {user_id}")

    pubsub_gateway = RedisPubSubGateway()
    try:
        uow_factory = get_unit_of_work_factory(pubsub_gateway)

        try:
            user = await user_repo.get(user_id)
            timezone = user.settings.timezone if user.settings else None
        except Exception:
            timezone = None

        target_date = get_current_date(timezone)
        now = get_current_datetime()
        evaluation_time = now.replace(second=0, microsecond=0)
        previous_date = target_date - dt_timedelta(days=1)

        def evaluate_day_alarms(
            day: DayEntity,
            *,
            snoozed_only: bool,
        ) -> None:
            for alarm in day.alarms:
                if alarm.status in (
                    value_objects.AlarmStatus.CANCELLED,
                    value_objects.AlarmStatus.TRIGGERED,
                ):
                    continue
                if alarm.status == value_objects.AlarmStatus.SNOOZED:
                    if (
                        alarm.snoozed_until is None
                        or alarm.snoozed_until > evaluation_time
                    ):
                        continue
                elif snoozed_only:
                    continue
                if alarm.datetime is None or alarm.datetime > evaluation_time:
                    continue
                day.update_alarm_status(
                    alarm.id,
                    value_objects.AlarmStatus.TRIGGERED,
                )

        async with uow_factory.create(user_id) as uow:
            for day_date, snoozed_only in (
                (target_date, False),
                (previous_date, True),
            ):
                try:
                    day_id = DayEntity.id_from_date_and_user(day_date, user_id)
                    day = await uow.day_ro_repo.get(day_id)
                except Exception as exc:
                    logger.debug(
                        "No day found for user %s on %s (%s)",
                        user_id,
                        day_date,
                        exc,
                    )
                    continue

                if not day.alarms:
                    continue

                evaluate_day_alarms(day, snoozed_only=snoozed_only)

                if day.has_events():
                    uow.add(day)

        logger.info("Alarm evaluation completed for user %s", user_id)
    finally:
        await pubsub_gateway.close()


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

            current_time = get_current_time(user.settings.timezone)
            current_hour = current_time.hour
            current_minute = current_time.minute

            time_matches = (
                current_hour == overview_hour
                and current_minute >= overview_minute
                and current_minute < overview_minute + 15
            )

            if not time_matches:
                continue

            ro_repos = ro_repo_factory.create(user.id)
            push_notification_repo: PushNotificationRepositoryReadOnlyProtocol = (
                ro_repos.push_notification_ro_repo
            )

            get_current_date(user.settings.timezone)
            today_start = get_current_datetime_in_timezone(user.settings.timezone)
            today_start = today_start.replace(hour=0, minute=0, second=0, microsecond=0)

            existing_notifications = await push_notification_repo.search(
                value_objects.PushNotificationQuery(
                    sent_after=today_start,
                    status="sent",
                )
            )

            morning_overview_sent_today = any(
                n.triggered_by == "morning_overview" for n in existing_notifications
            )

            if morning_overview_sent_today:
                logger.debug(
                    f"Morning overview already sent today for user {user.id}, skipping"
                )
                continue

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
            logger.exception(f"Error evaluating morning overview for user {user_id}")

    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def process_brain_dump_item_task(
    user_id: UUID,
    day_date: str,
    item_id: UUID,
) -> None:
    """Process a brain dump item for a specific user."""
    logger.info("Starting brain dump processing for user %s item %s", user_id, item_id)

    try:
        date = dt_date.fromisoformat(day_date)
    except ValueError:
        logger.warning(
            "Invalid brain dump date %s for user %s item %s",
            day_date,
            user_id,
            item_id,
        )
        return

    pubsub_gateway = RedisPubSubGateway()
    try:
        handler = get_process_brain_dump_handler(
            user_id=user_id,
            uow_factory=get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=get_read_only_repository_factory(),
        )

        try:
            await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item_id))
            logger.debug(
                "Brain dump processing completed for user %s item %s",
                user_id,
                item_id,
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Error processing brain dump for user %s item %s",
                user_id,
                item_id,
            )
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


register_worker_event_handlers()
