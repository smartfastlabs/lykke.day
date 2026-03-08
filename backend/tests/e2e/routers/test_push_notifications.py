"""E2E tests for push notifications search endpoints."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from lykke.domain.entities import PushNotificationEntity, PushSubscriptionEntity
from lykke.infrastructure.gateways import web_push
from lykke.infrastructure.repositories import (
    PushNotificationRepository,
    PushSubscriptionRepository,
)


@pytest.mark.asyncio
async def test_search_push_notifications_filters_by_sent_at(
    authenticated_client,
):
    client, user = await authenticated_client()
    repo = PushNotificationRepository(user=user)

    now = datetime.now(UTC)
    in_range = PushNotificationEntity(
        user_id=user.id,
        push_subscription_ids=[],
        content='{"title":"Hello","body":"World"}',
        status="success",
        sent_at=now - timedelta(minutes=30),
    )
    out_of_range = PushNotificationEntity(
        user_id=user.id,
        push_subscription_ids=[],
        content='{"title":"Old","body":"Notification"}',
        status="success",
        sent_at=now - timedelta(days=2),
    )
    await repo.put(in_range)
    await repo.put(out_of_range)

    response = client.post(
        "/push-notifications/",
        json={
            "limit": 50,
            "offset": 0,
            "filters": {
                "sent_after": (now - timedelta(days=1)).isoformat(),
                "sent_before": (now + timedelta(minutes=1)).isoformat(),
                "order_by": "sent_at",
                "order_by_desc": True,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    item_ids = {item["id"] for item in data["items"]}
    assert str(in_range.id) in item_ids
    assert str(out_of_range.id) not in item_ids


@pytest.mark.asyncio
async def test_send_test_push_to_single_subscription(authenticated_client, monkeypatch):
    client, user = await authenticated_client()
    repo = PushSubscriptionRepository(user=user)
    sent_subscription_ids: list[str] = []

    subscription = PushSubscriptionEntity(
        id=uuid4(),
        user_id=user.id,
        device_name="Test Device 1",
        endpoint="https://example.com/push/1",
        p256dh="p256dh_key_1",
        auth="auth_key_1",
    )
    other_subscription = PushSubscriptionEntity(
        id=uuid4(),
        user_id=user.id,
        device_name="Test Device 2",
        endpoint="https://example.com/push/2",
        p256dh="p256dh_key_2",
        auth="auth_key_2",
    )
    await repo.put(subscription)
    await repo.put(other_subscription)

    async def _send_notification(*, subscription: PushSubscriptionEntity, content: object) -> None:
        _ = content
        sent_subscription_ids.append(str(subscription.id))

    monkeypatch.setattr(web_push, "send_notification", _send_notification)

    response = client.post(f"/push/subscriptions/{subscription.id}/test-push/")

    assert response.status_code == 200
    assert response.json() == {"subscription_id": str(subscription.id)}
    assert sent_subscription_ids == [str(subscription.id)]
