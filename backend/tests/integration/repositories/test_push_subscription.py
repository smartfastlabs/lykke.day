"""Integration tests for PushSubscriptionRepository."""

from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from planned.core.exceptions import exceptions
from planned.domain.entities import PushSubscription
from planned.infrastructure.repositories import PushSubscriptionRepository


@pytest.mark.asyncio
async def test_get(push_subscription_repo, test_user):
    """Test getting a push subscription by ID."""
    subscription = PushSubscription(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        device_name="Test Device",
        endpoint="https://example.com/push",
        p256dh="p256dh_key",
        auth="auth_key",
    )
    await push_subscription_repo.put(subscription)
    
    result = await push_subscription_repo.get(subscription.id)
    
    assert result.id == subscription.id
    assert result.device_name == "Test Device"


@pytest.mark.asyncio
async def test_get_not_found(push_subscription_repo):
    """Test getting a non-existent push subscription raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await push_subscription_repo.get(str(uuid4()))


@pytest.mark.asyncio
async def test_put(push_subscription_repo, test_user):
    """Test creating a new push subscription."""
    subscription = PushSubscription(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        device_name="New Device",
        endpoint="https://example.com/push",
        p256dh="p256dh_key",
        auth="auth_key",
    )
    
    result = await push_subscription_repo.put(subscription)
    
    assert result.device_name == "New Device"
    assert result.endpoint == "https://example.com/push"


@pytest.mark.asyncio
async def test_all(push_subscription_repo, test_user):
    """Test getting all push subscriptions."""
    sub1 = PushSubscription(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        device_name="Device 1",
        endpoint="https://example.com/push1",
        p256dh="p256dh_key1",
        auth="auth_key1",
    )
    sub2 = PushSubscription(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        device_name="Device 2",
        endpoint="https://example.com/push2",
        p256dh="p256dh_key2",
        auth="auth_key2",
    )
    await push_subscription_repo.put(sub1)
    await push_subscription_repo.put(sub2)
    
    all_subs = await push_subscription_repo.all()
    
    sub_ids = [s.id for s in all_subs]
    assert sub1.id in sub_ids
    assert sub2.id in sub_ids


@pytest.mark.asyncio
async def test_user_isolation(push_subscription_repo, test_user, create_test_user):
    """Test that different users' push subscriptions are properly isolated."""
    subscription = PushSubscription(
        id=str(uuid4()),
        user_uuid=test_user.uuid,
        device_name="User1 Device",
        endpoint="https://example.com/push",
        p256dh="p256dh_key",
        auth="auth_key",
    )
    await push_subscription_repo.put(subscription)
    
    # Create another user
    user2 = await create_test_user()
    push_subscription_repo2 = PushSubscriptionRepository(user_uuid=user2.uuid)
    
    # User2 should not see user1's subscription
    with pytest.raises(exceptions.NotFoundError):
        await push_subscription_repo2.get(subscription.id)

