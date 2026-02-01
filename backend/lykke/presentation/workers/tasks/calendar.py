"""Calendar-related background worker tasks."""

from typing import Protocol
from uuid import UUID

from loguru import logger

from lykke.application.commands.calendar import (
    SubscribeCalendarCommand,
    SyncAllCalendarsCommand,
    SyncCalendarCommand,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_google_gateway,
    get_read_only_repository_factory,
    get_subscribe_calendar_handler,
    get_sync_all_calendars_handler,
    get_sync_calendar_handler,
    get_unit_of_work_factory,
)


class _CalendarHandler(Protocol):
    async def handle(self, command: object) -> None: ...


@broker.task  # type: ignore[untyped-decorator]
async def sync_calendar_task(
    user_id: UUID,
    *,
    handler: _CalendarHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    google_gateway: GoogleCalendarGatewayProtocol | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Sync all calendar entries for a specific user.

    This is an event-triggered task - enqueued when user requests a sync.

    Args:
        user_id: The user ID to sync calendars for.
    """
    logger.info(f"Starting calendar sync for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        sync_handler = handler or get_sync_all_calendars_handler(
            user_id=user_id,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            google_gateway=google_gateway or get_google_gateway(),
        )

        await sync_handler.handle(SyncAllCalendarsCommand())

        logger.info(f"Calendar sync completed for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def sync_single_calendar_task(
    user_id: UUID,
    calendar_id: UUID,
    *,
    handler: _CalendarHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    google_gateway: GoogleCalendarGatewayProtocol | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
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

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        sync_handler = handler or get_sync_calendar_handler(
            user_id=user_id,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            google_gateway=google_gateway or get_google_gateway(),
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
    *,
    handler: _CalendarHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    google_gateway: GoogleCalendarGatewayProtocol | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
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

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        subscribe_handler = handler or get_subscribe_calendar_handler(
            user_id=user_id,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            google_gateway=google_gateway or get_google_gateway(),
        )

        ro_factory = ro_repo_factory or get_read_only_repository_factory()
        ro_repos = ro_factory.create(user_id)
        calendar = await ro_repos.calendar_ro_repo.get(calendar_id)

        await subscribe_handler.handle(SubscribeCalendarCommand(calendar=calendar))

        logger.info(
            f"Calendar resubscription completed for user {user_id}, calendar {calendar_id}"
        )
    finally:
        await pubsub_gateway.close()
