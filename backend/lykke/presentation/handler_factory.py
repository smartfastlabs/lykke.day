"""Factories for creating command and query handlers consistently."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, overload

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.commands.calendar import (
    ResetCalendarDataHandler,
    ResetCalendarSyncHandler,
    ResyncCalendarHandler,
    SubscribeCalendarHandler,
    SyncAllCalendarsHandler,
    SyncCalendarHandler,
    UnsubscribeCalendarHandler,
)
from lykke.application.commands.day.reschedule_day import RescheduleDayHandler
from lykke.application.commands.day.schedule_day import ScheduleDayHandler
from lykke.application.commands.notifications import (
    MorningOverviewHandler,
    SmartNotificationHandler,
)
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.queries import (
    ComputeTaskRiskHandler,
    GenerateUseCasePromptHandler,
    GetDayContextHandler,
    GetLLMPromptContextHandler,
    PreviewDayHandler,
)
from lykke.application.queries.base import BaseQueryHandler
from lykke.infrastructure.gateways import GoogleCalendarGateway, WebPushGateway

if TYPE_CHECKING:
    from uuid import UUID

    from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
    from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
    from lykke.application.unit_of_work import (
        ReadOnlyRepositories,
        ReadOnlyRepositoryFactory,
        UnitOfWorkFactory,
    )

QueryHandlerT = TypeVar("QueryHandlerT", bound=BaseQueryHandler)
CommandHandlerT = TypeVar("CommandHandlerT", bound=BaseCommandHandler)


def _default_google_gateway() -> GoogleCalendarGatewayProtocol:
    return GoogleCalendarGateway()


def _default_web_push_gateway() -> WebPushGatewayProtocol:
    return WebPushGateway()


QueryHandlerProvider = Callable[["QueryHandlerFactory"], BaseQueryHandler]
CommandHandlerProvider = Callable[["CommandHandlerFactory"], BaseCommandHandler]


def _build_get_llm_prompt_context_handler(
    factory: QueryHandlerFactory,
) -> GetLLMPromptContextHandler:
    return GetLLMPromptContextHandler(
        factory.ro_repos,
        factory.user_id,
        factory.create(GetDayContextHandler),
    )


DEFAULT_QUERY_HANDLER_REGISTRY: dict[type[BaseQueryHandler], QueryHandlerProvider] = {
    GetLLMPromptContextHandler: _build_get_llm_prompt_context_handler,
}


class QueryHandlerFactory:
    """Factory for query handlers with explicit dependency wiring."""

    def __init__(
        self,
        *,
        user_id: UUID,
        ro_repo_factory: ReadOnlyRepositoryFactory,
        ro_repos: ReadOnlyRepositories | None = None,
        registry: dict[type[BaseQueryHandler], QueryHandlerProvider] | None = None,
    ) -> None:
        self.user_id = user_id
        self._ro_repos = ro_repos or ro_repo_factory.create(user_id)
        self._registry = registry or DEFAULT_QUERY_HANDLER_REGISTRY

    @property
    def ro_repos(self) -> ReadOnlyRepositories:
        return self._ro_repos

    @overload
    def create(
        self, handler_class: type[GetLLMPromptContextHandler]
    ) -> GetLLMPromptContextHandler: ...

    @overload
    def create(self, handler_class: type[QueryHandlerT]) -> QueryHandlerT: ...

    def create(self, handler_class: type[BaseQueryHandler]) -> BaseQueryHandler:
        provider = self._registry.get(handler_class)
        if provider is None:
            return handler_class(self._ro_repos, self.user_id)
        return provider(self)


def _build_schedule_day_handler(
    factory: CommandHandlerFactory,
) -> ScheduleDayHandler:
    return ScheduleDayHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.query_factory.create(PreviewDayHandler),
    )


def _build_reschedule_day_handler(
    factory: CommandHandlerFactory,
) -> RescheduleDayHandler:
    return RescheduleDayHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.create(ScheduleDayHandler),
    )


def _build_sync_calendar_handler(
    factory: CommandHandlerFactory,
) -> SyncCalendarHandler:
    return SyncCalendarHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
    )


def _build_sync_all_calendars_handler(
    factory: CommandHandlerFactory,
) -> SyncAllCalendarsHandler:
    return SyncAllCalendarsHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.create(SyncCalendarHandler),
    )


def _build_subscribe_calendar_handler(
    factory: CommandHandlerFactory,
) -> SubscribeCalendarHandler:
    return SubscribeCalendarHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
    )


def _build_unsubscribe_calendar_handler(
    factory: CommandHandlerFactory,
) -> UnsubscribeCalendarHandler:
    return UnsubscribeCalendarHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
    )


def _build_resync_calendar_handler(
    factory: CommandHandlerFactory,
) -> ResyncCalendarHandler:
    return ResyncCalendarHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
        factory.create(SyncCalendarHandler),
    )


def _build_reset_calendar_data_handler(
    factory: CommandHandlerFactory,
) -> ResetCalendarDataHandler:
    return ResetCalendarDataHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
    )


def _build_reset_calendar_sync_handler(
    factory: CommandHandlerFactory,
) -> ResetCalendarSyncHandler:
    return ResetCalendarSyncHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.google_gateway,
        factory.create(SyncCalendarHandler),
    )


def _build_send_push_notification_handler(
    factory: CommandHandlerFactory,
) -> SendPushNotificationHandler:
    return SendPushNotificationHandler(
        ro_repos=factory.ro_repos,
        uow_factory=factory.uow_factory,
        user_id=factory.user_id,
        web_push_gateway=factory.web_push_gateway,
    )


def _build_smart_notification_handler(
    factory: CommandHandlerFactory,
) -> SmartNotificationHandler:
    return SmartNotificationHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.query_factory.create(GetLLMPromptContextHandler),
        factory.query_factory.create(GenerateUseCasePromptHandler),
        factory.create(SendPushNotificationHandler),
    )


def _build_morning_overview_handler(
    factory: CommandHandlerFactory,
) -> MorningOverviewHandler:
    return MorningOverviewHandler(
        factory.ro_repos,
        factory.uow_factory,
        factory.user_id,
        factory.query_factory.create(GetLLMPromptContextHandler),
        factory.query_factory.create(ComputeTaskRiskHandler),
        factory.query_factory.create(GenerateUseCasePromptHandler),
        factory.create(SendPushNotificationHandler),
    )


DEFAULT_COMMAND_HANDLER_REGISTRY: dict[
    type[BaseCommandHandler], CommandHandlerProvider
] = {
    ScheduleDayHandler: _build_schedule_day_handler,
    RescheduleDayHandler: _build_reschedule_day_handler,
    SyncCalendarHandler: _build_sync_calendar_handler,
    SyncAllCalendarsHandler: _build_sync_all_calendars_handler,
    SubscribeCalendarHandler: _build_subscribe_calendar_handler,
    UnsubscribeCalendarHandler: _build_unsubscribe_calendar_handler,
    ResyncCalendarHandler: _build_resync_calendar_handler,
    ResetCalendarDataHandler: _build_reset_calendar_data_handler,
    ResetCalendarSyncHandler: _build_reset_calendar_sync_handler,
    SendPushNotificationHandler: _build_send_push_notification_handler,
    SmartNotificationHandler: _build_smart_notification_handler,
    MorningOverviewHandler: _build_morning_overview_handler,
}


class CommandHandlerFactory:
    """Factory for command handlers with explicit dependency wiring."""

    def __init__(
        self,
        *,
        user_id: UUID,
        ro_repo_factory: ReadOnlyRepositoryFactory,
        uow_factory: UnitOfWorkFactory,
        ro_repos: ReadOnlyRepositories | None = None,
        query_factory: QueryHandlerFactory | None = None,
        google_gateway_provider: Callable[[], GoogleCalendarGatewayProtocol]
        | None = None,
        web_push_gateway_provider: Callable[[], WebPushGatewayProtocol] | None = None,
        registry: dict[type[BaseCommandHandler], CommandHandlerProvider] | None = None,
    ) -> None:
        self.user_id = user_id
        self.uow_factory = uow_factory
        self._ro_repos = ro_repos or ro_repo_factory.create(user_id)
        self.query_factory = query_factory or QueryHandlerFactory(
            user_id=user_id,
            ro_repo_factory=ro_repo_factory,
            ro_repos=self._ro_repos,
        )
        self._registry = registry or DEFAULT_COMMAND_HANDLER_REGISTRY
        self._google_gateway_provider = (
            google_gateway_provider or _default_google_gateway
        )
        self._web_push_gateway_provider = (
            web_push_gateway_provider or _default_web_push_gateway
        )
        self._google_gateway: GoogleCalendarGatewayProtocol | None = None
        self._web_push_gateway: WebPushGatewayProtocol | None = None

    @property
    def ro_repos(self) -> ReadOnlyRepositories:
        return self._ro_repos

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
        self, handler_class: type[SmartNotificationHandler]
    ) -> SmartNotificationHandler: ...

    @overload
    def create(
        self, handler_class: type[MorningOverviewHandler]
    ) -> MorningOverviewHandler: ...

    @overload
    def create(self, handler_class: type[CommandHandlerT]) -> CommandHandlerT: ...

    def create(self, handler_class: type[BaseCommandHandler]) -> BaseCommandHandler:
        provider = self._registry.get(handler_class)
        if provider is None:
            return handler_class(self._ro_repos, self.uow_factory, self.user_id)
        return provider(self)
