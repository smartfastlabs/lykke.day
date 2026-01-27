"""Unit tests for DomainEventHandler base behavior."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.events.handlers.base import DomainEventHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.events.base import DomainEvent
from tests.support.dobles import create_read_only_repos_double


@dataclass(frozen=True, kw_only=True)
class _TestEvent(DomainEvent):
    payload: str


@dataclass(frozen=True, kw_only=True)
class _EntityEvent(DomainEvent):
    entity: object | None = None


@pytest.mark.asyncio
async def test_extract_user_id_from_event_entity() -> None:
    user_id = uuid4()
    entity = type("Entity", (), {"user_id": user_id})()
    event = _EntityEvent(user_id="not-a-uuid", entity=entity)  # type: ignore[arg-type]

    extracted = DomainEventHandler._extract_user_id(event)

    assert extracted == user_id


@pytest.mark.asyncio
async def test_extract_user_id_returns_none_for_non_uuid_entity() -> None:
    entity = type("Entity", (), {"user_id": "not-a-uuid"})()
    event = _EntityEvent(user_id="not-a-uuid", entity=entity)  # type: ignore[arg-type]

    extracted = DomainEventHandler._extract_user_id(event)

    assert extracted is None


@pytest.mark.asyncio
async def test_dispatch_ignores_non_domain_event() -> None:
    DomainEventHandler.clear_registry()

    await DomainEventHandler._dispatch_event(sender=None, event="not-an-event")


@pytest.mark.asyncio
async def test_dispatch_skips_event_without_uuid_user_id() -> None:
    DomainEventHandler.clear_registry()
    handled: list[DomainEvent] = []

    class _Handler(DomainEventHandler):
        handles = [_TestEvent]

        async def handle(self, event: DomainEvent) -> None:
            handled.append(event)

    ro_repos = create_read_only_repos_double()
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    DomainEventHandler.register_all_handlers(ro_repo_factory=ro_factory)

    event = _TestEvent(user_id="not-a-uuid", payload="ping")  # type: ignore[arg-type]
    await DomainEventHandler._dispatch_event(sender=None, event=event)

    assert handled == []


@pytest.mark.asyncio
async def test_dispatch_warns_when_ro_repo_factory_missing() -> None:
    DomainEventHandler.clear_registry()

    class _Handler(DomainEventHandler):
        handles = [_TestEvent]

        async def handle(self, event: DomainEvent) -> None:
            raise AssertionError("Should not be called without ro_repo_factory")

    DomainEventHandler.register_all_handlers(ro_repo_factory=None, uow_factory=None)
    event = _TestEvent(user_id=uuid4(), payload="ping")

    await DomainEventHandler._dispatch_event(sender=None, event=event)


@pytest.mark.asyncio
async def test_dispatch_event_creates_handler_instances() -> None:
    DomainEventHandler.clear_registry()
    handled: list[DomainEvent] = []

    class _Handler(DomainEventHandler):
        handles = [_TestEvent]

        async def handle(self, event: DomainEvent) -> None:
            handled.append(event)

    user_id = uuid4()
    ro_repos = create_read_only_repos_double()
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)
    uow_factory = InstanceDouble(
        f"{UnitOfWorkFactory.__module__}.{UnitOfWorkFactory.__name__}"
    )

    DomainEventHandler.register_all_handlers(
        ro_repo_factory=ro_factory,
        uow_factory=uow_factory,
    )

    event = _TestEvent(user_id=user_id, payload="ping")
    await DomainEventHandler._dispatch_event(sender=None, event=event)

    assert handled == [event]


def test_clear_registry_resets_handlers() -> None:
    DomainEventHandler.clear_registry()

    class _Handler(DomainEventHandler):
        handles = [_TestEvent]

        async def handle(self, event: DomainEvent) -> None:
            raise AssertionError("Should not be invoked in this test")

    assert DomainEventHandler._handler_classes

    DomainEventHandler.clear_registry()

    assert DomainEventHandler._handler_classes == []


def test_init_subclass_skips_handlers_without_handles() -> None:
    DomainEventHandler.clear_registry()

    class _Handler(DomainEventHandler):
        handles: list[type[DomainEvent]] = []

        async def handle(self, event: DomainEvent) -> None:
            raise AssertionError("Not used")

    assert DomainEventHandler._handler_classes == []
