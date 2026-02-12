"""Unit tests for SendPushNotificationHandler."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity, UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
    create_web_push_gateway_double,
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
        endpoint=f"https://example.com/push/{uuid4()}",
        p256dh="p256dh",
        auth="auth",
    )


@pytest.mark.asyncio
async def test_send_push_notification_skips_without_subscriptions() -> None:
    user_id = uuid4()
    handler = SendPushNotificationHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
        gateway_factory=_GatewayFactory(create_web_push_gateway_double()),
    )

    await handler.handle(SendPushNotificationCommand(subscriptions=[], content="hi"))


@pytest.mark.asyncio
async def test_send_push_notification_tracks_success() -> None:
    user_id = uuid4()
    uow = create_uow_double()
    web_push_gateway = create_web_push_gateway_double()
    sent: list[PushSubscriptionEntity] = []

    async def send_notification(
        *, subscription: PushSubscriptionEntity, content: object
    ) -> None:
        sent.append(subscription)

    web_push_gateway.send_notification = send_notification
    subscription = _build_subscription(user_id)
    handler = SendPushNotificationHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    payload = value_objects.NotificationPayload(
        title="Hello",
        body="World",
        actions=[],
        data={"type": "test"},
    )
    await handler.handle(
        SendPushNotificationCommand(subscriptions=[subscription], content=payload)
    )

    assert sent == [subscription]
    assert len(uow.created) == 1
    notification = uow.created[0]
    assert notification.status == "success"
    assert notification.push_subscription_ids == [subscription.id]


@pytest.mark.asyncio
async def test_send_push_notification_tracks_partial_failures() -> None:
    user_id = uuid4()
    uow = create_uow_double()
    web_push_gateway = create_web_push_gateway_double()
    subscription_ok = _build_subscription(user_id)
    subscription_fail = _build_subscription(user_id)

    async def send_notification(
        *, subscription: PushSubscriptionEntity, content: object
    ) -> None:
        if subscription.id == subscription_fail.id:
            raise RuntimeError("send failed")

    web_push_gateway.send_notification = send_notification
    handler = SendPushNotificationHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    await handler.handle(
        SendPushNotificationCommand(
            subscriptions=[subscription_ok, subscription_fail],
            content={"message": "hi"},
        )
    )

    notification = uow.created[0]
    assert notification.status == "partial_failure"
    assert notification.error_message is not None


@pytest.mark.asyncio
async def test_send_push_notification_tracks_all_failures() -> None:
    user_id = uuid4()
    uow = create_uow_double()
    web_push_gateway = create_web_push_gateway_double()

    async def send_notification(
        *, subscription: PushSubscriptionEntity, content: object
    ) -> None:
        raise RuntimeError("send failed")

    web_push_gateway.send_notification = send_notification
    subscription = _build_subscription(user_id)
    handler = SendPushNotificationHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    await handler.handle(
        SendPushNotificationCommand(
            subscriptions=[subscription],
            content="hi",
            message="hello",
        )
    )

    notification = uow.created[0]
    assert notification.status == "failed"


@pytest.mark.asyncio
async def test_send_push_notification_includes_click_target_url() -> None:
    """Verify push payload includes url for service worker notificationclick handler."""
    user_id = uuid4()
    uow = create_uow_double()
    web_push_gateway = create_web_push_gateway_double()
    captured_content: list[dict[str, Any]] = []

    async def send_notification(
        *, subscription: PushSubscriptionEntity, content: object
    ) -> None:
        _ = subscription
        if isinstance(content, dict):
            captured_content.append(dict(content))
        else:
            captured_content.append({"raw": content})

    web_push_gateway.send_notification = send_notification
    subscription = _build_subscription(user_id)
    handler = SendPushNotificationHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
        gateway_factory=_GatewayFactory(web_push_gateway),
    )

    payload = value_objects.NotificationPayload(
        title="Task reminder",
        body="Your task is ready",
        actions=[],
    )
    await handler.handle(
        SendPushNotificationCommand(subscriptions=[subscription], content=payload)
    )

    assert len(captured_content) == 1
    content = captured_content[0]
    assert "url" in content
    assert content["url"].startswith("/me/notifications/")

    notification = uow.created[0]
    expected_id = str(notification.id)
    assert content["url"] == f"/me/notifications/{expected_id}"
