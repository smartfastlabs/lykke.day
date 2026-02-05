"""Shared helpers for background worker tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import UUID

from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import DayRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import GoogleCalendarGateway, RedisPubSubGateway
from lykke.infrastructure.repositories import DayRepository
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.workers.tasks.post_commit_workers import WorkersToSchedule
from lykke.presentation.workers.tasks.registry import WorkerRegistry

if TYPE_CHECKING:
    from lykke.application.commands import ScheduleDayHandler
    from lykke.application.commands.brain_dump import ProcessBrainDumpHandler
    from lykke.application.commands.calendar import (
        SubscribeCalendarHandler,
        SyncAllCalendarsHandler,
        SyncCalendarHandler,
    )
    from lykke.application.commands.day import TriggerAlarmsForUserHandler
    from lykke.application.commands.message import ProcessInboundSmsHandler
    from lykke.application.commands.onboarding import ProcessSmsOnboardingHandler
    from lykke.application.commands.notifications import (
        CalendarEntryNotificationHandler,
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
    return SqlAlchemyUnitOfWorkFactory(
        pubsub_gateway=gateway,
        workers_to_schedule_factory=lambda: WorkersToSchedule(WorkerRegistry()),
    )


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    from lykke.infrastructure.repository_factories import SqlAlchemyReadOnlyRepositoryFactory

    return SqlAlchemyReadOnlyRepositoryFactory()


def get_identity_access() -> UnauthenticatedIdentityAccess:
    """Get identity access for workers (cross-user lookups allowed)."""
    return UnauthenticatedIdentityAccess()


def get_day_repository(user_id: UUID) -> DayRepositoryReadOnlyProtocol:
    """Get a DayRepository instance scoped to the given user."""
    from lykke.presentation.api.routers.dependencies.user import build_synthetic_user

    user = build_synthetic_user(user_id)
    return cast("DayRepositoryReadOnlyProtocol", DayRepository(user=user))


async def load_user(user_id: UUID) -> UserEntity:
    """Load a user entity by ID for worker tasks."""
    identity_access = get_identity_access()
    user = await identity_access.get_user_by_id(user_id)
    if user is None:
        raise NotFoundError(f"User with id {user_id} not found")
    return user


def get_sync_all_calendars_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SyncAllCalendarsHandler:
    """Get a SyncAllCalendarsHandler instance for a user."""
    from lykke.application.commands.calendar import SyncAllCalendarsHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SyncAllCalendarsHandler)


def get_sync_calendar_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SyncCalendarHandler:
    """Get a SyncCalendarHandler instance for a user."""
    from lykke.application.commands.calendar import SyncCalendarHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SyncCalendarHandler)


def get_subscribe_calendar_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
    google_gateway: GoogleCalendarGatewayProtocol,
) -> SubscribeCalendarHandler:
    """Get a SubscribeCalendarHandler instance for a user."""
    from lykke.application.commands.calendar import SubscribeCalendarHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SubscribeCalendarHandler)


def get_schedule_day_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance for a user."""
    from lykke.application.commands import ScheduleDayHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ScheduleDayHandler)


def get_smart_notification_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> SmartNotificationHandler:
    """Get a SmartNotificationHandler instance for a user."""
    from lykke.application.commands.notifications import SmartNotificationHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(SmartNotificationHandler)


def get_morning_overview_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> MorningOverviewHandler:
    """Get a MorningOverviewHandler instance for a user."""
    from lykke.application.commands.notifications import MorningOverviewHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(MorningOverviewHandler)


def get_calendar_entry_notification_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> CalendarEntryNotificationHandler:
    """Get a CalendarEntryNotificationHandler instance for a user."""
    from lykke.application.commands.notifications import (
        CalendarEntryNotificationHandler,
    )
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(CalendarEntryNotificationHandler)


def get_process_brain_dump_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ProcessBrainDumpHandler:
    """Get a ProcessBrainDumpHandler instance for a user."""
    from lykke.application.commands.brain_dump import ProcessBrainDumpHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ProcessBrainDumpHandler)


def get_process_inbound_sms_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ProcessInboundSmsHandler:
    """Get a ProcessInboundSmsHandler instance for a user."""
    from lykke.application.commands.message import ProcessInboundSmsHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ProcessInboundSmsHandler)


def get_process_sms_onboarding_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> ProcessSmsOnboardingHandler:
    """Get a ProcessSmsOnboardingHandler instance for a user."""
    from lykke.application.commands.onboarding import ProcessSmsOnboardingHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ProcessSmsOnboardingHandler)


def get_trigger_alarms_for_user_handler(
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> TriggerAlarmsForUserHandler:
    """Get a TriggerAlarmsForUserHandler instance for a user."""
    from lykke.application.commands.day import TriggerAlarmsForUserHandler
    from lykke.presentation.handler_factory import CommandHandlerFactory

    factory = CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(TriggerAlarmsForUserHandler)
