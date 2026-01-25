"""E2E tests for push notifications search endpoints."""

from datetime import UTC, datetime, timedelta

import pytest

from lykke.domain.entities import PushNotificationEntity
from lykke.infrastructure.repositories import PushNotificationRepository


@pytest.mark.asyncio
async def test_search_push_notifications_filters_by_sent_at(
    authenticated_client,
):
    client, user = await authenticated_client()
    repo = PushNotificationRepository(user_id=user.id)

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
