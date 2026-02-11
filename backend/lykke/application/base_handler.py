"""Base handler class shared by commands, queries, and event handlers."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from inspect import get_annotations
from typing import TYPE_CHECKING, Any, cast

from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories

if TYPE_CHECKING:
    from collections.abc import Callable

    from lykke.application.handler_factory_protocols import (
        BaseFactory,
        CommandHandlerFactoryProtocol,
        GatewayFactoryProtocol,
        ReadOnlyRepositoryFactoryProtocol,
    )
    from lykke.application.unit_of_work import (
        UnitOfWorkFactory,
    )
    from lykke.domain.entities import UserEntity


class BaseHandler:
    """Base class for handlers with dependency wiring via annotations.

    This class provides common initialization for command handlers, query handlers,
    and event handlers. Dependencies are populated from factories based on type
    annotations declared on the handler class (or its base classes).

    Usage:
        class MyHandler(BaseHandler):
            async def handle(self, command: MyCommand) -> None:
                # Access repositories as needed - they are wired from annotations
                task = await self.task_ro_repo.get(command.task_id)
                day = await self.day_ro_repo.get(command.day_id)
    """

    # Repository attribute suffix used to identify repository lookups
    _RO_REPO_SUFFIX = "_ro_repo"

    command_factory: CommandHandlerFactoryProtocol | None
    gateway_factory: GatewayFactoryProtocol | None
    _uow_factory: UnitOfWorkFactory | None
    _repository_factory: ReadOnlyRepositoryFactoryProtocol
    _repositories: ReadOnlyRepositories | None

    def __init__(
        self,
        user: UserEntity,
        *,
        command_factory: CommandHandlerFactoryProtocol | None = None,
        uow_factory: UnitOfWorkFactory | None = None,
        gateway_factory: GatewayFactoryProtocol | None = None,
        repository_factory: ReadOnlyRepositoryFactoryProtocol | None = None,
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
        self._repositories = None
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

    def _wire_dependencies(self) -> None:
        """Populate annotated dependencies from factories when available."""
        factories: list[BaseFactory] = [
            _RepositoryDependencyFactory(
                self._get_ro_repos, _build_repo_type_map(ReadOnlyRepositories)
            )
        ]
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
