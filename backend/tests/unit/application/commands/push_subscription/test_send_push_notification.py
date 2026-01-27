"""Unit tests for SendPushNotificationHandler."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.push_subscription import (
    SendPushNotificationCommand,
    SendPushNotificationHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
    create_web_push_gateway_double,
)


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
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        create_web_push_gateway_double(),
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
        create_read_only_repos_double(),
        create_uow_factory_double(uow),
        user_id,
        web_push_gateway,
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
        create_read_only_repos_double(),
        create_uow_factory_double(uow),
        user_id,
        web_push_gateway,
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
        create_read_only_repos_double(),
        create_uow_factory_double(uow),
        user_id,
        web_push_gateway,
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
