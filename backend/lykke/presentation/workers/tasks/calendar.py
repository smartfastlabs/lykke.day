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
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_google_gateway,
    get_read_only_repository_factory,
    get_subscribe_calendar_handler,
    get_sync_all_calendars_handler,
    get_sync_calendar_handler,
    get_unit_of_work_factory,
    load_user,
)


class _SyncAllCalendarsHandler(Protocol):
    user: UserEntity

    async def handle(self, command: SyncAllCalendarsCommand) -> object: ...


class _SyncCalendarHandler(Protocol):
    user: UserEntity

    async def handle(self, command: SyncCalendarCommand) -> object: ...


class _SubscribeCalendarHandler(Protocol):
    user: UserEntity

    async def handle(self, command: SubscribeCalendarCommand) -> object: ...


@broker.task  # type: ignore[untyped-decorator]
async def sync_calendar_task(
    user_id: UUID,
    *,
    handler: _SyncAllCalendarsHandler | None = None,
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
        resolved_handler: _SyncAllCalendarsHandler
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for calendar sync task {user_id}")
                return

            resolved_handler = get_sync_all_calendars_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
                google_gateway=google_gateway or get_google_gateway(),
            )
        else:
            resolved_handler = handler

        await resolved_handler.handle(SyncAllCalendarsCommand())

        logger.info(f"Calendar sync completed for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task  # type: ignore[untyped-decorator]
async def sync_single_calendar_task(
    user_id: UUID,
    calendar_id: UUID,
    *,
    handler: _SyncCalendarHandler | None = None,
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
        resolved_handler: _SyncCalendarHandler
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(
                    f"User not found for single calendar sync task {user_id}"
                )
                return

            resolved_handler = get_sync_calendar_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
                google_gateway=google_gateway or get_google_gateway(),
            )
        else:
            resolved_handler = handler

        await resolved_handler.handle(SyncCalendarCommand(calendar_id=calendar_id))

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
    handler: _SubscribeCalendarHandler | None = None,
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
        resolved_handler: _SubscribeCalendarHandler
        user: UserEntity
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(
                    f"User not found for calendar resubscription task {user_id}"
                )
                return

            resolved_handler = get_subscribe_calendar_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
                google_gateway=google_gateway or get_google_gateway(),
            )
        else:
            resolved_handler = handler
            user = handler.user

        ro_factory = ro_repo_factory or get_read_only_repository_factory()
        ro_repos = ro_factory.create(user)
        calendar = await ro_repos.calendar_ro_repo.get(calendar_id)

        await resolved_handler.handle(SubscribeCalendarCommand(calendar=calendar))

        logger.info(
            f"Calendar resubscription completed for user {user_id}, calendar {calendar_id}"
        )
    finally:
        await pubsub_gateway.close()
