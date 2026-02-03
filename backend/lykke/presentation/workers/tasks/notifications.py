"""Notification-related background worker tasks."""

from collections.abc import Callable
from datetime import datetime as dt_datetime, time as dt_time
from typing import Annotated, Protocol, TypeVar
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.notifications import (
    CalendarEntryNotificationCommand,
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
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_calendar_entry_notification_handler,
    get_morning_overview_handler,
    get_read_only_repository_factory,
    get_smart_notification_handler,
    get_unit_of_work_factory,
    get_user_repository,
    load_user,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


_CommandT = TypeVar("_CommandT", contravariant=True)


class _NotificationHandler(Protocol[_CommandT]):
    user: UserEntity

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
    users_with_llm = [
        user for user in users if user.settings and user.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")

    task = enqueue_task or evaluate_smart_notification_task
    for user in users_with_llm:
        await task.kiq(user_id=user.id, triggered_by="scheduled")

    logger.info(
        f"Enqueued smart notification evaluation tasks for {len(users_with_llm)} users"
    )


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_calendar_entry_notifications_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
) -> None:
    """Evaluate calendar entry reminders for all eligible users."""
    logger.info("Starting calendar entry notification evaluation for all users")
    users = await user_repo.all()
    eligible_users = [
        user
        for user in users
        if user.settings
        and user.settings.calendar_entry_notification_settings.enabled
        and user.settings.calendar_entry_notification_settings.rules
    ]
    logger.info(
        f"Found {len(eligible_users)} users eligible for calendar entry notifications",
    )

    for user in eligible_users:
        logger.info(
            f"Enqueued calendar entry notification evaluation task for user {user.id}"
        )
        await evaluate_calendar_entry_notifications_task.kiq(
            user_id=user.id, triggered_by="scheduled"
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
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for smart notification task {user_id}")
                return
            resolved_handler = get_smart_notification_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler
            user = resolved_handler.user

        try:
            await resolved_handler.handle(
                SmartNotificationCommand(
                    user=user,
                    triggered_by=triggered_by,
                )
            )
            logger.debug(f"Smart notification evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error evaluating smart notification for user {user_id}")

    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_calendar_entry_notifications_task(
    user_id: UUID,
    triggered_by: str | None = None,
    *,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Evaluate calendar entry reminders for a specific user."""
    logger.info(f"Starting calendar entry notification evaluation for user {user_id}")
    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        try:
            user = await load_user(user_id)
        except Exception:
            logger.warning(
                f"User not found for calendar entry notification task {user_id}"
            )
            return
        handler = get_calendar_entry_notification_handler(
            user=user,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
        )
        try:
            await handler.handle(
                CalendarEntryNotificationCommand(
                    user=user,
                    triggered_by=triggered_by,
                )
            )
            logger.debug(
                f"Calendar entry notification evaluation completed for user {user_id}",
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                f"Error evaluating calendar entry notifications for user {user_id}"
            )
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
            overview_time = user.settings.morning_overview_time
            if not overview_time:
                continue

            overview_hour = overview_time.hour
            overview_minute = overview_time.minute

            current_time = current_time_provider(user.settings.timezone)
            current_hour = current_time.hour
            current_minute = current_time.minute

            time_matches = (
                current_hour == overview_hour
                and current_minute >= overview_minute
                and current_minute < overview_minute + 15
            )

            if not time_matches:
                continue

            ro_repos = ro_repo_factory.create(user)
            push_notification_repo: PushNotificationRepositoryReadOnlyProtocol = (
                ro_repos.push_notification_ro_repo
            )

            get_current_date(user.settings.timezone)
            today_start = current_datetime_provider(user.settings.timezone)
            today_start = today_start.replace(hour=0, minute=0, second=0, microsecond=0)

            existing_notifications = await push_notification_repo.search(
                value_objects.PushNotificationQuery(
                    sent_after=today_start,
                    triggered_by="morning_overview",
                )
            )

            morning_overview_sent_today = bool(existing_notifications)

            if morning_overview_sent_today:
                logger.debug(
                    f"Morning overview already sent today for user {user.id}, skipping",
                )
                continue

            await task.kiq(user_id=user.id)
            logger.info(f"Enqueued morning overview for user {user.id}")

        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error checking morning overview for user {user.id}")

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
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for morning overview task {user_id}")
                return
            resolved_handler = get_morning_overview_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler
            user = resolved_handler.user

        try:
            await resolved_handler.handle(MorningOverviewCommand(user=user))
            logger.debug(f"Morning overview evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error evaluating morning overview for user {user_id}")

    finally:
        await pubsub_gateway.close()
