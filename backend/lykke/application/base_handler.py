"""Base handler class shared by commands, queries, and event handlers."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from inspect import get_annotations
from typing import TYPE_CHECKING, Any, cast

from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, ReadWriteRepositories

if TYPE_CHECKING:
    from collections.abc import Callable

    from lykke.application.handler_factory_protocols import (
        BaseFactory,
        CommandHandlerFactoryProtocol,
        GatewayFactoryProtocol,
        ReadOnlyRepositoryFactoryProtocol,
    )
    from lykke.application.repositories import (
        AuditLogRepositoryReadOnlyProtocol,
        AuthTokenRepositoryReadOnlyProtocol,
        BotPersonalityRepositoryReadOnlyProtocol,
        BrainDumpRepositoryReadOnlyProtocol,
        CalendarEntryRepositoryReadOnlyProtocol,
        CalendarEntrySeriesRepositoryReadOnlyProtocol,
        CalendarRepositoryReadOnlyProtocol,
        DayRepositoryReadOnlyProtocol,
        DayTemplateRepositoryReadOnlyProtocol,
        FactoidRepositoryReadOnlyProtocol,
        MessageRepositoryReadOnlyProtocol,
        PushNotificationRepositoryReadOnlyProtocol,
        PushSubscriptionRepositoryReadOnlyProtocol,
        RoutineDefinitionRepositoryReadOnlyProtocol,
        RoutineRepositoryReadOnlyProtocol,
        SmsLoginCodeRepositoryReadOnlyProtocol,
        TacticRepositoryReadOnlyProtocol,
        TaskDefinitionRepositoryReadOnlyProtocol,
        TaskRepositoryReadOnlyProtocol,
        TimeBlockDefinitionRepositoryReadOnlyProtocol,
        TriggerRepositoryReadOnlyProtocol,
        UseCaseConfigRepositoryReadOnlyProtocol,
        UserRepositoryReadOnlyProtocol,
    )
    from lykke.application.unit_of_work import (
        ReadWriteRepositoryFactory,
        UnitOfWorkFactory,
    )
    from lykke.domain.entities import UserEntity


class BaseHandler:
    """Base class for handlers with lazy repository access.

    This class provides common initialization for command handlers, query handlers,
    and event handlers. Repository access is lazy via __getattr__, so handlers only
    access the repositories they actually need.

    Usage:
        class MyHandler(BaseHandler):
            async def handle(self, command: MyCommand) -> None:
                # Access repositories as needed - they're resolved lazily
                task = await self.task_ro_repo.get(command.task_id)
                day = await self.day_ro_repo.get(command.day_id)
    """

    # Repository attribute suffix used to identify repository lookups
    _RO_REPO_SUFFIX = "_ro_repo"
    _RW_REPO_SUFFIX = "_rw_repo"

    # Type hints for static analysis (repos are accessed lazily at runtime)
    audit_log_ro_repo: AuditLogRepositoryReadOnlyProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    bot_personality_ro_repo: BotPersonalityRepositoryReadOnlyProtocol
    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
    tactic_ro_repo: TacticRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol
    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol
    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol
    sms_login_code_ro_repo: SmsLoginCodeRepositoryReadOnlyProtocol

    command_factory: CommandHandlerFactoryProtocol | None
    gateway_factory: GatewayFactoryProtocol | None
    _uow_factory: UnitOfWorkFactory | None
    _repository_factory: ReadOnlyRepositoryFactoryProtocol
    _rw_repository_factory: ReadWriteRepositoryFactory | None
    _repositories: ReadOnlyRepositories | None
    _rw_repositories: ReadWriteRepositories | None

    def __init__(
        self,
        user: UserEntity,
        *,
        command_factory: CommandHandlerFactoryProtocol | None = None,
        uow_factory: UnitOfWorkFactory | None = None,
        gateway_factory: GatewayFactoryProtocol | None = None,
        repository_factory: ReadOnlyRepositoryFactoryProtocol | None = None,
        readwrite_repository_factory: ReadWriteRepositoryFactory | None = None,
    ) -> None:
        """Initialize the handler with its dependencies.

        Args:
            user: The user entity for this handler instance
        """
        self.user = user
        self.command_factory = command_factory
        self.gateway_factory = gateway_factory
        self._uow_factory = uow_factory

        if repository_factory is None:
            raise ValueError("BaseHandler requires repository_factory.")

        self._repository_factory = repository_factory
        self._rw_repository_factory = readwrite_repository_factory
        self._repositories = None
        self._rw_repositories = None
        self._gateway_overrides: dict[type[object], object] = {}
        self._wire_dependencies()

    @property
    def google_gateway(self) -> GoogleCalendarGatewayProtocol:
        """Return the configured Google Calendar gateway."""
        return cast(
            "GoogleCalendarGatewayProtocol",
            self._get_gateway(GoogleCalendarGatewayProtocol),
        )

    @google_gateway.setter
    def google_gateway(self, gateway: GoogleCalendarGatewayProtocol) -> None:
        self._gateway_overrides[GoogleCalendarGatewayProtocol] = gateway

    @property
    def web_push_gateway(self) -> WebPushGatewayProtocol:
        """Return the configured web push gateway."""
        return cast(
            "WebPushGatewayProtocol",
            self._get_gateway(WebPushGatewayProtocol),
        )

    @web_push_gateway.setter
    def web_push_gateway(self, gateway: WebPushGatewayProtocol) -> None:
        self._gateway_overrides[WebPushGatewayProtocol] = gateway

    @property
    def sms_gateway(self) -> SMSProviderProtocol:
        """Return the configured SMS gateway."""
        return cast(
            "SMSProviderProtocol",
            self._get_gateway(SMSProviderProtocol),
        )

    @sms_gateway.setter
    def sms_gateway(self, gateway: SMSProviderProtocol) -> None:
        self._gateway_overrides[SMSProviderProtocol] = gateway

    def _get_gateway(self, dependency_type: type[object]) -> object:
        if dependency_type in self._gateway_overrides:
            return self._gateway_overrides[dependency_type]
        if self.gateway_factory is None:
            raise AttributeError("No gateway_factory configured.")
        if not self.gateway_factory.can_create(dependency_type):
            raise AttributeError(
                f"No gateway configured for {dependency_type.__name__}"
            )
        return self.gateway_factory.create(dependency_type)

    def __getattr__(self, name: str) -> Any:
        """Provide lazy access to repositories from the container.

        This allows handlers to access repositories like self.task_ro_repo
        without explicitly wiring them in __init__. The repository is looked
        up from the repository factory on first access.

        Args:
            name: Attribute name being accessed

        Returns:
            The repository if it exists on the repositories

        Raises:
            AttributeError: If the attribute doesn't exist on the repositories
        """
        # Only intercept repository lookups
        if name.endswith(self._RO_REPO_SUFFIX):
            try:
                ro_repos = self._get_ro_repos()
                return getattr(ro_repos, name)
            except AttributeError:
                pass
        if name.endswith(self._RW_REPO_SUFFIX):
            try:
                rw_repos = self._get_rw_repos()
                return getattr(rw_repos, name)
            except AttributeError:
                pass

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def _wire_dependencies(self) -> None:
        """Populate annotated dependencies from factories when available."""
        factories: list[BaseFactory] = [
            _RepositoryDependencyFactory(
                self._get_ro_repos, _build_repo_type_map(ReadOnlyRepositories)
            )
        ]
        if self._rw_repository_factory is not None:
            factories.append(
                _RepositoryDependencyFactory(
                    self._get_rw_repos,
                    _build_repo_type_map(ReadWriteRepositories),
                )
            )
        if self.gateway_factory is not None:
            factories.append(self.gateway_factory)
        if self.command_factory is not None:
            factories.append(self.command_factory)
        query_factory = getattr(self.command_factory, "query_factory", None)
        if query_factory is not None:
            factories.append(query_factory)

        for cls in type(self).mro():
            annotations = get_annotations(cls, eval_str=False)
            if not annotations:
                continue
            for name, annotation in annotations.items():
                if name in self.__dict__:
                    continue

                resolved = self._resolve_annotation(cls, annotation)
                if resolved is None:
                    continue

                for factory in factories:
                    if factory.can_create(resolved):
                        setattr(self, name, factory.create(resolved))
                        break

    def _get_ro_repos(self) -> ReadOnlyRepositories:
        if self._repositories is None:
            self._repositories = self._repository_factory.create(self.user)
        return self._repositories

    def _get_rw_repos(self) -> ReadWriteRepositories:
        if self._rw_repository_factory is None:
            raise AttributeError("No ReadWriteRepositoryFactory configured.")
        if self._rw_repositories is None:
            self._rw_repositories = self._rw_repository_factory.create(self.user)
        return self._rw_repositories

    @staticmethod
    def _resolve_annotation(owner: type[object], annotation: object) -> type | None:
        if isinstance(annotation, str):
            module = sys.modules.get(owner.__module__)
            if module is None:
                return None
            return getattr(module, annotation, None)
        if isinstance(annotation, type):
            return annotation
        return None


@dataclass(frozen=True)
class _StaticReadOnlyRepositoryFactory:
    ro_repos: ReadOnlyRepositories

    def create(self, user: UserEntity) -> ReadOnlyRepositories:
        _ = user
        return self.ro_repos


def _build_repo_type_map(repo_protocol: type[object]) -> dict[type[object], str]:
    annotations = get_annotations(repo_protocol, eval_str=False)
    return {
        annotation: name
        for name, annotation in annotations.items()
        if isinstance(annotation, type)
    }


class _RepositoryDependencyFactory:
    def __init__(
        self,
        get_repos: Callable[[], object],
        repo_type_map: dict[type[object], str],
    ) -> None:
        self._get_repos = get_repos
        self._repo_type_map = repo_type_map

    def can_create(self, dependency_type: type[object]) -> bool:
        return dependency_type in self._repo_type_map

    def create(self, dependency_type: type[object]) -> object:
        repo_name = self._repo_type_map[dependency_type]
        return getattr(self._get_repos(), repo_name)
