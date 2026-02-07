"""Unit tests for CalendarEntryPushNotificationHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.events.handlers.calendar_entry_push_notifications import (
    CalendarEntryPushNotificationHandler,
)
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import (
    CalendarEntryEntity,
    PushSubscriptionEntity,
    UserEntity,
)
from lykke.domain.events.base import DomainEvent
from lykke.domain.events.calendar_entry_events import (
    CalendarEntryCreatedEvent,
    CalendarEntryDeletedEvent,
    CalendarEntryUpdatedEvent,
)
from tests.support.dobles import (
    create_calendar_entry_repo_double,
    create_push_subscription_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _GatewayFactory:
    def __init__(self, web_push_gateway: WebPushGatewayProtocol) -> None:
        self._web_push_gateway = web_push_gateway

    def can_create(self, dependency_type: type[object]) -> bool:
        return dependency_type is WebPushGatewayProtocol

    def create(self, dependency_type: type[object]) -> object:
        _ = dependency_type
        return self._web_push_gateway


def _build_subscription(user_id: Any) -> PushSubscriptionEntity:
    return PushSubscriptionEntity(
        user_id=user_id,
        endpoint="https://example.com/push/entry",
        p256dh="p256dh",
        auth="auth",
    )


def _build_calendar_entry(
    user_id: Any,
    *,
    attendance_status: value_objects.CalendarEntryAttendanceStatus | None = None,
) -> CalendarEntryEntity:
    return CalendarEntryEntity(
        user_id=user_id,
        name="Daily standup",
        calendar_id=uuid4(),
        platform_id="event-1",
        platform="google",
        status="confirmed",
        attendance_status=attendance_status,
        starts_at=datetime(2025, 11, 27, 10, 0, tzinfo=UTC),
        ends_at=datetime(2025, 11, 27, 10, 30, tzinfo=UTC),
        frequency=value_objects.TaskFrequency.ONCE,
    )


@pytest.mark.asyncio
async def test_calendar_entry_handler_skips_without_subscriptions() -> None:
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(user_id)
    push_subscription_repo = create_push_subscription_repo_double()

    async def no_subscriptions() -> list[PushSubscriptionEntity]:
        return []

    push_subscription_repo.all = no_subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryCreatedEvent(
        user_id=user_id, calendar_entry_id=calendar_entry.id
    )
    await handler.handle(event)


@pytest.mark.asyncio
async def test_calendar_entry_handler_returns_without_uow_factory() -> None:
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(user_id)
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=None,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryCreatedEvent(
        user_id=user_id, calendar_entry_id=calendar_entry.id
    )
    await handler.handle(event)


@pytest.mark.asyncio
async def test_calendar_entry_handler_loads_entry_and_sends() -> None:
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(user_id)
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry

    send_calls: list[PushSubscriptionEntity] = []

    class _WebPushGateway(WebPushGatewayProtocol):
        async def send_notification(
            self,
            subscription: PushSubscriptionEntity,
            content: object,
        ) -> None:
            _ = content
            send_calls.append(subscription)

    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryUpdatedEvent(
        user_id=user_id,
        calendar_entry_id=calendar_entry.id,
        update_object=value_objects.CalendarEntryUpdateObject(name="Updated"),
    )
    await handler.handle(event)

    assert send_calls


@pytest.mark.asyncio
async def test_calendar_entry_handler_skips_when_not_going() -> None:
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(
        user_id, attendance_status=value_objects.CalendarEntryAttendanceStatus.NOT_GOING
    )
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry

    send_calls: list[PushSubscriptionEntity] = []

    class _WebPushGateway(WebPushGatewayProtocol):
        async def send_notification(
            self,
            subscription: PushSubscriptionEntity,
            content: object,
        ) -> None:
            _ = content
            send_calls.append(subscription)

    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryUpdatedEvent(
        user_id=user_id,
        calendar_entry_id=calendar_entry.id,
        update_object=value_objects.CalendarEntryUpdateObject(name="Updated"),
    )
    await handler.handle(event)

    assert send_calls == []


@pytest.mark.asyncio
async def test_calendar_entry_handler_skips_when_marked_missed_via_update_object() -> None:
    """Ensure we don't notify when user marks an entry MISSED.

    Handlers run BEFORE commit; reloading the entry can be stale. This test
    simulates a stale repo read (attendance_status is None) while the update
    event carries the new MISSED status.
    """
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(user_id, attendance_status=None)
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry

    send_calls: list[PushSubscriptionEntity] = []

    class _WebPushGateway(WebPushGatewayProtocol):
        async def send_notification(
            self,
            subscription: PushSubscriptionEntity,
            content: object,
        ) -> None:
            _ = content
            send_calls.append(subscription)

    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryUpdatedEvent(
        user_id=user_id,
        calendar_entry_id=calendar_entry.id,
        update_object=value_objects.CalendarEntryUpdateObject(
            attendance_status=value_objects.CalendarEntryAttendanceStatus.MISSED
        ),
    )
    await handler.handle(event)

    assert send_calls == []


@pytest.mark.asyncio
async def test_calendar_entry_handler_uses_snapshot_on_delete() -> None:
    user_id = uuid4()
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        raise AssertionError("Should not fetch entry for deleted event")

    calendar_entry_repo.get = get_entry
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryDeletedEvent(
        user_id=user_id,
        calendar_entry_id=uuid4(),
        entry_snapshot={
            "id": "entry",
            "name": "Old event",
            "starts_at": datetime(2025, 11, 27, 9, 0, tzinfo=UTC).isoformat(),
            "ends_at": None,
            "calendar_id": str(uuid4()),
            "platform_id": "platform-id",
            "status": "cancelled",
        },
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_calendar_entry_handler_handles_missing_entry() -> None:
    user_id = uuid4()
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def raise_get(_: Any) -> CalendarEntryEntity:
        raise RuntimeError("not found")

    calendar_entry_repo.get = raise_get
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryCreatedEvent(user_id=user_id, calendar_entry_id=uuid4())
    await handler.handle(event)


@pytest.mark.asyncio
async def test_calendar_entry_handler_ignores_unknown_event() -> None:
    user_id = uuid4()

    @dataclass(frozen=True, kw_only=True)
    class _OtherEvent(DomainEvent):
        pass

    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=create_push_subscription_repo_double(),
        calendar_entry_repo=create_calendar_entry_repo_double(),
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    await handler.handle(_OtherEvent(user_id=user_id))


@pytest.mark.asyncio
async def test_calendar_entry_handler_logs_when_entry_data_missing() -> None:
    user_id = uuid4()
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def return_none(_: Any) -> None:
        return None

    calendar_entry_repo.get = return_none
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    event = CalendarEntryUpdatedEvent(
        user_id=user_id,
        calendar_entry_id=uuid4(),
        update_object=value_objects.CalendarEntryUpdateObject(name="Updated"),
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_calendar_entry_handler_handles_payload_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    calendar_entry = _build_calendar_entry(user_id)
    push_subscription_repo = create_push_subscription_repo_double()

    async def subscriptions() -> list[PushSubscriptionEntity]:
        return [_build_subscription(user_id)]

    push_subscription_repo.all = subscriptions
    calendar_entry_repo = create_calendar_entry_repo_double()

    async def get_entry(_: Any) -> CalendarEntryEntity:
        return calendar_entry

    calendar_entry_repo.get = get_entry
    web_push_gateway = _WebPushGateway()
    ro_repos = create_read_only_repos_double(
        push_subscription_repo=push_subscription_repo,
        calendar_entry_repo=calendar_entry_repo,
    )
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    uow_factory = create_uow_factory_double(create_uow_double())
    handler = CalendarEntryPushNotificationHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
        uow_factory=uow_factory,
    )
    handler.send_push_notification_handler = SendPushNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    def raise_payload(*_: Any, **__: Any) -> None:
        raise RuntimeError("payload error")

    monkeypatch.setattr(
        "lykke.application.events.handlers.calendar_entry_push_notifications."
        "build_notification_payload_for_calendar_entry_change",
        raise_payload,
    )

    event = CalendarEntryCreatedEvent(
        user_id=user_id, calendar_entry_id=calendar_entry.id
    )
    await handler.handle(event)


class _WebPushGateway(WebPushGatewayProtocol):
    async def send_notification(
        self,
        subscription: PushSubscriptionEntity,
        content: object,
    ) -> None:
        _ = subscription
        _ = content
