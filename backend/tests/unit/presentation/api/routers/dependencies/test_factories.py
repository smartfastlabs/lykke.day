"""Tests for router dependency factories."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.queries.preview_llm_snapshot import PreviewLLMSnapshotHandler
from lykke.domain.entities import UserEntity
from lykke.presentation.api.routers.dependencies.factories import (
    create_query_handler,
    create_query_handler_websocket,
)
from lykke.presentation.handler_factory import QueryHandlerFactory


class _RepositoryFactory:
    def create(self, user: UserEntity) -> object:
        _ = user
        return SimpleNamespace()


class _UnitOfWorkFactory:
    def create(self, user: UserEntity) -> object:
        _ = user
        return object()


def test_create_query_handler_wires_gateway_factory(monkeypatch) -> None:
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    captured: dict[str, object] = {}
    sentinel = object()

    def _fake_create(self: QueryHandlerFactory, handler_class: type) -> object:
        _ = handler_class
        captured["gateway_factory"] = self.gateway_factory
        return sentinel

    monkeypatch.setattr(QueryHandlerFactory, "create", _fake_create)
    dependency = create_query_handler(PreviewLLMSnapshotHandler)
    result = dependency(
        user=user,
        ro_repo_factory=_RepositoryFactory(),
        uow_factory=_UnitOfWorkFactory(),
    )

    assert result is sentinel
    gateway_factory = captured["gateway_factory"]
    assert gateway_factory is not None
    assert gateway_factory.can_create(LLMGatewayFactoryProtocol)


def test_create_query_handler_websocket_wires_gateway_factory(monkeypatch) -> None:
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    captured: dict[str, object] = {}
    sentinel = object()

    def _fake_create(self: QueryHandlerFactory, handler_class: type) -> object:
        _ = handler_class
        captured["gateway_factory"] = self.gateway_factory
        return sentinel

    monkeypatch.setattr(QueryHandlerFactory, "create", _fake_create)
    dependency = create_query_handler_websocket(PreviewLLMSnapshotHandler)
    result = dependency(
        user=user,
        ro_repo_factory=_RepositoryFactory(),
        uow_factory=_UnitOfWorkFactory(),
    )

    assert result is sentinel
    gateway_factory = captured["gateway_factory"]
    assert gateway_factory is not None
    assert gateway_factory.can_create(LLMGatewayFactoryProtocol)
