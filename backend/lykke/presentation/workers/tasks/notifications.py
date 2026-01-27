"""Notification-related background worker tasks."""

from collections.abc import Callable
from datetime import datetime as dt_datetime, time as dt_time
from typing import Annotated, Protocol, TypeVar
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.notifications import (
    KioskNotificationCommand,
    MorningOverviewCommand,
    SmartNotificationCommand,
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
)
from lykke.domain import value_objects
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_kiosk_notification_handler,
    get_morning_overview_handler,
    get_read_only_repository_factory,
    get_smart_notification_handler,
    get_unit_of_work_factory,
    get_user_repository,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


_CommandT = TypeVar("_CommandT", contravariant=True)


class _NotificationHandler(Protocol[_CommandT]):
    async def handle(self, command: _CommandT) -> None: ...


@broker.task(schedule=[{"cron": "0,19,20,30,50 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_smart_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    enqueue_task: _EnqueueTask | None = None,
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

    task = enqueue_task or evaluate_smart_notification_task
    for user in users_with_llm:
        # Enqueue a sub-task for each user
        await task.kiq(user_id=user.id, triggered_by="scheduled")

    logger.info(
        f"Enqueued smart notification evaluation tasks for {len(users_with_llm)} users"
    )


@broker.task(schedule=[{"cron": "0,19,20,30,50 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_kiosk_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Evaluate kiosk notifications for all users with LLM provider configured.

    Runs at :00, :20, :30, and :50 each hour to check kiosk notifications.
    """
    logger.info("Starting kiosk notification evaluation for all users")

    users = await user_repo.all()
    # Filter to users with LLM provider configured
    users_with_llm = [
        user for user in users if user.settings and user.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")

    task = enqueue_task or evaluate_kiosk_notification_task
    for user in users_with_llm:
        # Enqueue a sub-task for each user
        await task.kiq(user_id=user.id, triggered_by="scheduled")

    logger.info(
        f"Enqueued kiosk notification evaluation tasks for {len(users_with_llm)} users"
    )


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_smart_notification_task(
    user_id: UUID,
    triggered_by: str | None = None,
    *,
    handler: _NotificationHandler[SmartNotificationCommand] | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
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

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        resolved_handler: _NotificationHandler[SmartNotificationCommand]
        if handler is None:
            resolved_handler = get_smart_notification_handler(
                user_id=user_id,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler

        try:
            await resolved_handler.handle(
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


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_kiosk_notification_task(
    user_id: UUID,
    triggered_by: str | None = None,
    *,
    handler: _NotificationHandler[KioskNotificationCommand] | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Evaluate and send kiosk notification for a specific user.

    This task can be triggered by:
    - Scheduled task (every 10 minutes)

    Args:
        user_id: The user ID to evaluate kiosk notifications for
        triggered_by: How this task was triggered (e.g., "scheduled")
    """
    logger.info(f"Starting kiosk notification evaluation for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        resolved_handler: _NotificationHandler[KioskNotificationCommand]
        if handler is None:
            resolved_handler = get_kiosk_notification_handler(
                user_id=user_id,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler

        try:
            await resolved_handler.handle(
                KioskNotificationCommand(
                    user_id=user_id,
                    triggered_by=triggered_by,
                )
            )
            logger.debug(f"Kiosk notification evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job - continue with other users
            logger.exception(f"Error evaluating kiosk notification for user {user_id}")

    finally:
        await pubsub_gateway.close()


@broker.task(schedule=[{"cron": "*/15 * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_morning_overviews_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    enqueue_task: _EnqueueTask | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    current_time_provider: Callable[[str | None], dt_time] | None = None,
    current_datetime_provider: Callable[[str | None], dt_datetime] | None = None,
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

    ro_repo_factory = ro_repo_factory or get_read_only_repository_factory()
    current_time_provider = current_time_provider or get_current_time
    current_datetime_provider = (
        current_datetime_provider or get_current_datetime_in_timezone
    )

    task = enqueue_task or evaluate_morning_overview_task
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
                    "Invalid morning_overview_time format for user %s: %s",
                    user.id,
                    overview_time_str,
                )
                continue

            # Get current time in user's timezone
            current_time = current_time_provider(user.settings.timezone)
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

            get_current_date(user.settings.timezone)
            today_start = current_datetime_provider(user.settings.timezone)
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
                    "Morning overview already sent today for user %s, skipping",
                    user.id,
                )
                continue

            # Enqueue the morning overview task
            await task.kiq(user_id=user.id)
            logger.info("Enqueued morning overview for user %s", user.id)

        except Exception:  # pylint: disable=broad-except
            logger.exception("Error checking morning overview for user %s", user.id)

    logger.info("Completed morning overview evaluation for all users")


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_morning_overview_task(
    user_id: UUID,
    *,
    handler: _NotificationHandler[MorningOverviewCommand] | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Evaluate and send morning overview for a specific user.

    Args:
        user_id: The user ID to send morning overview for
    """
    logger.info(f"Starting morning overview evaluation for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        resolved_handler: _NotificationHandler[MorningOverviewCommand]
        if handler is None:
            resolved_handler = get_morning_overview_handler(
                user_id=user_id,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler

        try:
            await resolved_handler.handle(MorningOverviewCommand(user_id=user_id))
            logger.debug(f"Morning overview evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job
            logger.exception(f"Error evaluating morning overview for user {user_id}")

    finally:
        await pubsub_gateway.close()
