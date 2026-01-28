"""Shared helpers for background worker tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import UUID

from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import GoogleCalendarGateway, RedisPubSubGateway
from lykke.infrastructure.repositories import UserRepository

if TYPE_CHECKING:
    from lykke.application.commands import ScheduleDayHandler
    from lykke.application.commands.brain_dump import ProcessBrainDumpHandler
    from lykke.application.commands.calendar import (
        SubscribeCalendarHandler,
        SyncAllCalendarsHandler,
        SyncCalendarHandler,
    )
    from lykke.application.commands.notifications import (
        KioskNotificationHandler,
        MorningOverviewHandler,
        SmartNotificationHandler,
    )
    from lykke.presentation.handler_factory import CommandHandlerFactory


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
    from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory

    gateway = pubsub_gateway or RedisPubSubGateway()
    return SqlAlchemyUnitOfWorkFactory(pubsub_gateway=gateway)


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    from lykke.infrastructure.unit_of_work import SqlAlchemyReadOnlyRepositoryFactory

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
    from lykke.application.commands.calendar import SyncAllCalendarsHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.calendar import SyncCalendarHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.calendar import SubscribeCalendarHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands import ScheduleDayHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.notifications import SmartNotificationHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.notifications import KioskNotificationHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.notifications import MorningOverviewHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

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
    from lykke.application.commands.brain_dump import ProcessBrainDumpHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user_id=user_id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ProcessBrainDumpHandler)
