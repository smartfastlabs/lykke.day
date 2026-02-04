"""Factories for creating command and query handlers consistently."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast, overload

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.commands.brain_dump import ProcessBrainDumpHandler
from lykke.application.commands.calendar import (
    ResetCalendarDataHandler,
    ResetCalendarSyncHandler,
    ResyncCalendarHandler,
    SubscribeCalendarHandler,
    SyncAllCalendarsHandler,
    SyncCalendarHandler,
    UnsubscribeCalendarHandler,
)
from lykke.application.commands.day import AddAlarmToDayHandler, UpdateDayHandler
from lykke.application.commands.day.reschedule_day import RescheduleDayHandler
from lykke.application.commands.day.schedule_day import ScheduleDayHandler
from lykke.application.commands.google import HandleGoogleLoginCallbackHandler
from lykke.application.commands.message import ProcessInboundSmsHandler
from lykke.application.commands.notifications import (
    CalendarEntryNotificationHandler,
    MorningOverviewHandler,
    SmartNotificationHandler,
)
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.commands.task import (
    CreateAdhocTaskHandler,
    DeleteTaskHandler,
    RecordTaskActionHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.identity import CurrentUserAccessProtocol
from lykke.application.queries import (
    ComputeTaskRiskHandler,
    GetDayContextHandler,
    GetLLMPromptContextHandler,
    PreviewDayHandler,
    PreviewLLMSnapshotHandler,
)
from lykke.application.queries.base import BaseQueryHandler
from lykke.infrastructure.gateways import (
    GoogleCalendarGateway,
    RedisPubSubGateway,
    TwilioGateway,
    WebPushGateway,
)
from lykke.infrastructure.user_scoped import CurrentUserAccess

if TYPE_CHECKING:
    from lykke.application.events.handlers import DomainEventHandler
    from lykke.application.handler_factory_protocols import GatewayFactoryProtocol
    from lykke.application.unit_of_work import (
        ReadOnlyRepositories,
        ReadOnlyRepositoryFactory,
        UnitOfWorkFactory,
    )
    from lykke.domain.entities import UserEntity

QueryHandlerT = TypeVar("QueryHandlerT", bound=BaseQueryHandler)
CommandHandlerT = TypeVar("CommandHandlerT", bound=BaseCommandHandler)


def _default_google_gateway() -> GoogleCalendarGatewayProtocol:
    return GoogleCalendarGateway()


def _default_web_push_gateway() -> WebPushGatewayProtocol:
    return WebPushGateway()


def _default_sms_gateway() -> SMSProviderProtocol:
    return TwilioGateway()


def _default_llm_gateway_factory() -> LLMGatewayFactoryProtocol:
    from lykke.infrastructure.gateways.llm_gateway_factory import InfraLLMGatewayFactory

    return InfraLLMGatewayFactory()


def build_domain_event_handler(
    handler_class: type[DomainEventHandler],
    user: UserEntity,
    repository_factory: ReadOnlyRepositoryFactory,
    uow_factory: UnitOfWorkFactory | None,
) -> DomainEventHandler:
    """Construct a domain event handler with outer-layer dependencies."""
    command_factory = None
    if uow_factory is not None:
        command_factory = CommandHandlerFactory(
            user=user,
            ro_repo_factory=repository_factory,
            uow_factory=uow_factory,
        )

    return handler_class(
        user=user,
        repository_factory=repository_factory,
        uow_factory=uow_factory,
        command_factory=command_factory,
        gateway_factory=command_factory,
    )


QueryHandlerProvider = Callable[["QueryHandlerFactory"], BaseQueryHandler]
CommandHandlerProvider = Callable[["CommandHandlerFactory"], BaseCommandHandler]


def _build_get_llm_prompt_context_handler(
    factory: QueryHandlerFactory,
) -> GetLLMPromptContextHandler:
    return GetLLMPromptContextHandler(
        user=factory.user,
        command_factory=factory,
        gateway_factory=factory.gateway_factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_preview_llm_snapshot_handler(
    factory: QueryHandlerFactory,
) -> PreviewLLMSnapshotHandler:
    return PreviewLLMSnapshotHandler(
        user=factory.user,
        command_factory=factory,
        gateway_factory=factory.gateway_factory,
        repository_factory=factory.ro_repo_factory,
    )


DEFAULT_QUERY_HANDLER_REGISTRY: dict[type[BaseQueryHandler], QueryHandlerProvider] = {
    GetLLMPromptContextHandler: _build_get_llm_prompt_context_handler,
    PreviewLLMSnapshotHandler: _build_preview_llm_snapshot_handler,
}


class QueryHandlerFactory:
    """Factory for query handlers with explicit dependency wiring."""

    def __init__(
        self,
        *,
        user: UserEntity,
        ro_repo_factory: ReadOnlyRepositoryFactory,
        ro_repos: ReadOnlyRepositories | None = None,
        gateway_factory: GatewayFactoryProtocol | None = None,
        registry: dict[type[BaseQueryHandler], QueryHandlerProvider] | None = None,
    ) -> None:
        self.user = user
        self._ro_repo_factory = ro_repo_factory
        self._ro_repos = ro_repos or ro_repo_factory.create(user)
        self._gateway_factory = gateway_factory
        self._registry = registry or DEFAULT_QUERY_HANDLER_REGISTRY

    @property
    def ro_repos(self) -> ReadOnlyRepositories:
        return self._ro_repos

    @property
    def ro_repo_factory(self) -> ReadOnlyRepositoryFactory:
        return self._ro_repo_factory

    @property
    def gateway_factory(self) -> GatewayFactoryProtocol | None:
        return self._gateway_factory

    @overload
    def create(
        self, handler_class: type[GetLLMPromptContextHandler]
    ) -> GetLLMPromptContextHandler: ...

    @overload
    def create(self, handler_class: type[QueryHandlerT]) -> QueryHandlerT: ...

    @overload
    def create(self, handler_class: type[object]) -> object: ...

    def create(self, handler_class: type[object]) -> object:
        handler_type = cast("type[BaseQueryHandler]", handler_class)
        provider = self._registry.get(handler_type)
        if provider is None:
            return handler_type(
                user=self.user,
                command_factory=self,
                gateway_factory=self._gateway_factory,
                repository_factory=self._ro_repo_factory,
            )
        return provider(self)

    def can_create(self, handler_class: type[object]) -> bool:
        return issubclass(handler_class, BaseQueryHandler)


def _build_schedule_day_handler(
    factory: CommandHandlerFactory,
) -> ScheduleDayHandler:
    return ScheduleDayHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_reschedule_day_handler(
    factory: CommandHandlerFactory,
) -> RescheduleDayHandler:
    return RescheduleDayHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_update_day_handler(
    factory: CommandHandlerFactory,
) -> UpdateDayHandler:
    return UpdateDayHandler(
        user=factory.user,
        command_factory=factory,
        uow_factory=factory.uow_factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_sync_calendar_handler(
    factory: CommandHandlerFactory,
) -> SyncCalendarHandler:
    return SyncCalendarHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_sync_all_calendars_handler(
    factory: CommandHandlerFactory,
) -> SyncAllCalendarsHandler:
    return SyncAllCalendarsHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_subscribe_calendar_handler(
    factory: CommandHandlerFactory,
) -> SubscribeCalendarHandler:
    return SubscribeCalendarHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_unsubscribe_calendar_handler(
    factory: CommandHandlerFactory,
) -> UnsubscribeCalendarHandler:
    return UnsubscribeCalendarHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_resync_calendar_handler(
    factory: CommandHandlerFactory,
) -> ResyncCalendarHandler:
    return ResyncCalendarHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_reset_calendar_data_handler(
    factory: CommandHandlerFactory,
) -> ResetCalendarDataHandler:
    return ResetCalendarDataHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_reset_calendar_sync_handler(
    factory: CommandHandlerFactory,
) -> ResetCalendarSyncHandler:
    return ResetCalendarSyncHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_send_push_notification_handler(
    factory: CommandHandlerFactory,
) -> SendPushNotificationHandler:
    return SendPushNotificationHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_google_login_callback_handler(
    factory: CommandHandlerFactory,
) -> HandleGoogleLoginCallbackHandler:
    return HandleGoogleLoginCallbackHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_smart_notification_handler(
    factory: CommandHandlerFactory,
) -> SmartNotificationHandler:
    return SmartNotificationHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_calendar_entry_notification_handler(
    factory: CommandHandlerFactory,
) -> CalendarEntryNotificationHandler:
    return CalendarEntryNotificationHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_morning_overview_handler(
    factory: CommandHandlerFactory,
) -> MorningOverviewHandler:
    return MorningOverviewHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_process_brain_dump_handler(
    factory: CommandHandlerFactory,
) -> ProcessBrainDumpHandler:
    return ProcessBrainDumpHandler(
        user=factory.user,
        command_factory=factory,
        uow_factory=factory.uow_factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


def _build_process_inbound_sms_handler(
    factory: CommandHandlerFactory,
) -> ProcessInboundSmsHandler:
    return ProcessInboundSmsHandler(
        user=factory.user,
        uow_factory=factory.uow_factory,
        command_factory=factory,
        gateway_factory=factory,
        repository_factory=factory.ro_repo_factory,
    )


DEFAULT_COMMAND_HANDLER_REGISTRY: dict[
    type[BaseCommandHandler], CommandHandlerProvider
] = {
    ScheduleDayHandler: _build_schedule_day_handler,
    RescheduleDayHandler: _build_reschedule_day_handler,
    UpdateDayHandler: _build_update_day_handler,
    SyncCalendarHandler: _build_sync_calendar_handler,
    SyncAllCalendarsHandler: _build_sync_all_calendars_handler,
    SubscribeCalendarHandler: _build_subscribe_calendar_handler,
    UnsubscribeCalendarHandler: _build_unsubscribe_calendar_handler,
    ResyncCalendarHandler: _build_resync_calendar_handler,
    ResetCalendarDataHandler: _build_reset_calendar_data_handler,
    ResetCalendarSyncHandler: _build_reset_calendar_sync_handler,
    SendPushNotificationHandler: _build_send_push_notification_handler,
    HandleGoogleLoginCallbackHandler: _build_google_login_callback_handler,
    SmartNotificationHandler: _build_smart_notification_handler,
    CalendarEntryNotificationHandler: _build_calendar_entry_notification_handler,
    MorningOverviewHandler: _build_morning_overview_handler,
    ProcessBrainDumpHandler: _build_process_brain_dump_handler,
    ProcessInboundSmsHandler: _build_process_inbound_sms_handler,
}


class CommandHandlerFactory:
    """Factory for command handlers with explicit dependency wiring."""

    def __init__(
        self,
        *,
        user: UserEntity,
        ro_repo_factory: ReadOnlyRepositoryFactory,
        uow_factory: UnitOfWorkFactory,
        ro_repos: ReadOnlyRepositories | None = None,
        query_factory: QueryHandlerFactory | None = None,
        google_gateway_provider: Callable[[], GoogleCalendarGatewayProtocol]
        | None = None,
        web_push_gateway_provider: Callable[[], WebPushGatewayProtocol] | None = None,
        sms_gateway_provider: Callable[[], SMSProviderProtocol] | None = None,
        llm_gateway_factory_provider: Callable[[], LLMGatewayFactoryProtocol]
        | None = None,
        registry: dict[type[BaseCommandHandler], CommandHandlerProvider] | None = None,
    ) -> None:
        self.user = user
        self._ro_repo_factory = ro_repo_factory
        self.uow_factory = uow_factory
        self._ro_repos = ro_repos or ro_repo_factory.create(user)
        self.query_factory = query_factory or QueryHandlerFactory(
            user=user,
            ro_repo_factory=ro_repo_factory,
            ro_repos=self._ro_repos,
            gateway_factory=self,
        )
        self._registry = registry or DEFAULT_COMMAND_HANDLER_REGISTRY
        self._google_gateway_provider = (
            google_gateway_provider or _default_google_gateway
        )
        self._web_push_gateway_provider = (
            web_push_gateway_provider or _default_web_push_gateway
        )
        self._sms_gateway_provider = sms_gateway_provider or _default_sms_gateway
        self._llm_gateway_factory_provider = (
            llm_gateway_factory_provider or _default_llm_gateway_factory
        )
        self._google_gateway: GoogleCalendarGatewayProtocol | None = None
        self._web_push_gateway: WebPushGatewayProtocol | None = None
        self._sms_gateway: SMSProviderProtocol | None = None
        self._llm_gateway_factory: LLMGatewayFactoryProtocol | None = None

    @property
    def ro_repos(self) -> ReadOnlyRepositories:
        return self._ro_repos

    @property
    def ro_repo_factory(self) -> ReadOnlyRepositoryFactory:
        return self._ro_repo_factory

    @property
    def google_gateway(self) -> GoogleCalendarGatewayProtocol:
        if self._google_gateway is None:
            self._google_gateway = self._google_gateway_provider()
        return self._google_gateway

    @property
    def web_push_gateway(self) -> WebPushGatewayProtocol:
        if self._web_push_gateway is None:
            self._web_push_gateway = self._web_push_gateway_provider()
        return self._web_push_gateway

    @property
    def sms_gateway(self) -> SMSProviderProtocol:
        if self._sms_gateway is None:
            self._sms_gateway = self._sms_gateway_provider()
        return self._sms_gateway

    @property
    def llm_gateway_factory(self) -> LLMGatewayFactoryProtocol:
        if self._llm_gateway_factory is None:
            self._llm_gateway_factory = self._llm_gateway_factory_provider()
        return self._llm_gateway_factory

    @overload
    def create(self, handler_class: type[ScheduleDayHandler]) -> ScheduleDayHandler: ...

    @overload
    def create(
        self, handler_class: type[RescheduleDayHandler]
    ) -> RescheduleDayHandler: ...

    @overload
    def create(
        self, handler_class: type[SyncCalendarHandler]
    ) -> SyncCalendarHandler: ...

    @overload
    def create(
        self, handler_class: type[SyncAllCalendarsHandler]
    ) -> SyncAllCalendarsHandler: ...

    @overload
    def create(
        self, handler_class: type[SubscribeCalendarHandler]
    ) -> SubscribeCalendarHandler: ...

    @overload
    def create(
        self, handler_class: type[UnsubscribeCalendarHandler]
    ) -> UnsubscribeCalendarHandler: ...

    @overload
    def create(
        self, handler_class: type[ResyncCalendarHandler]
    ) -> ResyncCalendarHandler: ...

    @overload
    def create(
        self, handler_class: type[ResetCalendarDataHandler]
    ) -> ResetCalendarDataHandler: ...

    @overload
    def create(
        self, handler_class: type[ResetCalendarSyncHandler]
    ) -> ResetCalendarSyncHandler: ...

    @overload
    def create(
        self, handler_class: type[SendPushNotificationHandler]
    ) -> SendPushNotificationHandler: ...

    @overload
    def create(
        self, handler_class: type[HandleGoogleLoginCallbackHandler]
    ) -> HandleGoogleLoginCallbackHandler: ...

    @overload
    def create(
        self, handler_class: type[SmartNotificationHandler]
    ) -> SmartNotificationHandler: ...

    @overload
    def create(
        self, handler_class: type[MorningOverviewHandler]
    ) -> MorningOverviewHandler: ...

    @overload
    def create(
        self, handler_class: type[ProcessBrainDumpHandler]
    ) -> ProcessBrainDumpHandler: ...

    @overload
    def create(
        self, handler_class: type[ProcessInboundSmsHandler]
    ) -> ProcessInboundSmsHandler: ...

    @overload
    def create(self, handler_class: type[CommandHandlerT]) -> CommandHandlerT: ...

    @overload
    def create(self, handler_class: type[object]) -> object: ...

    def create(self, handler_class: type[object]) -> object:
        gateway_provider = self._gateway_provider_for_type(handler_class)
        if gateway_provider is not None:
            return gateway_provider()
        handler_type = cast("type[BaseCommandHandler]", handler_class)
        provider = self._registry.get(handler_type)
        if provider is None:
            return handler_type(
                user=self.user,
                uow_factory=self.uow_factory,
                command_factory=self,
                gateway_factory=self,
                repository_factory=self._ro_repo_factory,
            )
        return provider(self)

    def can_create(self, handler_class: type[object]) -> bool:
        if self._gateway_provider_for_type(handler_class) is not None:
            return True
        return issubclass(handler_class, BaseCommandHandler)

    def _gateway_provider_for_type(
        self, gateway_type: type[object]
    ) -> Callable[[], object] | None:
        return {
            GoogleCalendarGatewayProtocol: lambda: self.google_gateway,
            WebPushGatewayProtocol: lambda: self.web_push_gateway,
            SMSProviderProtocol: lambda: self.sms_gateway,
            LLMGatewayFactoryProtocol: lambda: self.llm_gateway_factory,
            CurrentUserAccessProtocol: lambda: CurrentUserAccess(user=self.user),
        }.get(gateway_type)
