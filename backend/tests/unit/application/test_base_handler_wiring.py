"""Tests for BaseHandler dependency auto-wiring."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

from lykke.application.base_handler import BaseHandler
from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.domain.entities import UserEntity


class _DummyCommand(Command):
    """Minimal command for wiring test."""


class _DummyQuery(Query):
    """Minimal query for wiring test."""


class _DummyCommandHandler(BaseCommandHandler[_DummyCommand, None]):
    async def handle(self, command: _DummyCommand) -> None:
        _ = command


class _DummyQueryHandler(BaseQueryHandler[_DummyQuery, None]):
    async def handle(self, query: _DummyQuery) -> None:
        _ = query


@dataclass
class _CommandFactory:
    handlers: dict[type[object], object]
    query_factory: object | None = None

    def can_create(self, handler_class: type[object]) -> bool:
        return handler_class in self.handlers

    def create(self, handler_class: type[object]) -> object:
        return self.handlers[handler_class]


@dataclass
class _QueryFactory:
    handler: object

    def can_create(self, handler_class: type[object]) -> bool:
        _ = handler_class
        return True

    def create(self, handler_class: type[object]) -> object:
        _ = handler_class
        return self.handler


@dataclass
class _GatewayFactory:
    llm_gateway_factory: LLMGatewayFactoryProtocol

    def can_create(self, gateway_type: type[object]) -> bool:
        return gateway_type is LLMGatewayFactoryProtocol

    def create(self, gateway_type: type[object]) -> object:
        _ = gateway_type
        return self.llm_gateway_factory


@dataclass
class _RepositoryFactory:
    ro_repos: object

    def create(self, user: UserEntity) -> object:
        _ = user
        return self.ro_repos


class _DummyHandler(BaseHandler):
    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    command_handler: _DummyCommandHandler
    query_handler: _DummyQueryHandler
    llm_gateway_factory: LLMGatewayFactoryProtocol


def test_base_handler_wires_dependencies() -> None:
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    repo_sentinel = object()
    ro_repos = SimpleNamespace(brain_dump_ro_repo=repo_sentinel)

    command_handler_sentinel = object()
    query_handler_sentinel = object()
    llm_gateway_factory_sentinel = object()

    handler = _DummyHandler(
        user=user,
        command_factory=_CommandFactory(
            handlers={_DummyCommandHandler: command_handler_sentinel},
            query_factory=_QueryFactory(handler=query_handler_sentinel),
        ),
        gateway_factory=_GatewayFactory(
            llm_gateway_factory=llm_gateway_factory_sentinel
        ),
        repository_factory=_RepositoryFactory(ro_repos=ro_repos),
    )

    assert handler.brain_dump_ro_repo is repo_sentinel
    assert handler.command_handler is command_handler_sentinel
    assert handler.query_handler is query_handler_sentinel
    assert handler.llm_gateway_factory is llm_gateway_factory_sentinel
