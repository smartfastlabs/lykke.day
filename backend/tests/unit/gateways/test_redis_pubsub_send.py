"""Unit tests for Redis PubSub sending messages through subscriptions."""

import asyncio
from uuid import uuid4

import pytest

from lykke.infrastructure.gateways.redis_pubsub import RedisPubSubGateway


@pytest.mark.asyncio
async def test_send_message_through_subscription() -> None:
    """Test sending a message through a subscription."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()
    message = {"event": "test", "data": "hello"}

    # Create two subscriptions - one to send, one to receive
    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub1:
        async with gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="auditlog"
        ) as sub2:
            await asyncio.sleep(0.1)

            # Send message through sub1
            await sub1.send_message(message)

            # Receive on both subscriptions (sender also receives)
            received1 = await sub1.get_message(timeout=2.0)
            received2 = await sub2.get_message(timeout=2.0)

            assert received1 is not None
            assert received1["event"] == "test"
            assert received2 is not None
            assert received2["event"] == "test"

    await gateway.close()


@pytest.mark.asyncio
async def test_bidirectional_communication() -> None:
    """Test bidirectional communication between two subscriptions."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub1:
        async with gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="auditlog"
        ) as sub2:
            await asyncio.sleep(0.1)

            # Sub1 sends message
            await sub1.send_message({"from": "sub1", "message": "hello sub2"})

            # Sub2 receives and responds
            msg = await sub2.get_message(timeout=2.0)
            assert msg is not None
            assert msg["from"] == "sub1"

            await sub2.send_message({"from": "sub2", "message": "hello sub1"})

            # Sub1 receives response (skip its own sent message)
            await sub1.get_message(timeout=2.0)  # Skip own message
            response = await sub1.get_message(timeout=2.0)
            assert response is not None
            assert response["from"] == "sub2"

    await gateway.close()


@pytest.mark.asyncio
async def test_send_message_after_close_raises_error() -> None:
    """Test that sending a message on a closed subscription raises an error."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    subscription = None
    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub:
        subscription = sub

    # Subscription is now closed
    with pytest.raises(RuntimeError, match="Cannot send message on closed subscription"):
        await subscription.send_message({"test": "message"})

    await gateway.close()


@pytest.mark.asyncio
async def test_send_and_publish_are_equivalent() -> None:
    """Test that send_message and publish_to_user_channel produce the same result."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()
    message1 = {"method": "send", "data": "test"}
    message2 = {"method": "publish", "data": "test"}

    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        await asyncio.sleep(0.1)

        # Send via subscription.send_message
        await subscription.send_message(message1)

        # Publish via gateway.publish_to_user_channel
        await gateway.publish_to_user_channel(
            user_id=user_id, channel_type="auditlog", message=message2
        )

        # Both should be received
        received1 = await subscription.get_message(timeout=2.0)
        received2 = await subscription.get_message(timeout=2.0)

        assert received1 is not None
        assert received1["method"] == "send"
        assert received2 is not None
        assert received2["method"] == "publish"

    await gateway.close()


@pytest.mark.asyncio
async def test_context_manager_cleanup() -> None:
    """Test that context manager properly cleans up resources."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    subscription = None
    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub:
        subscription = sub
        # Subscription should be active
        await subscription.send_message({"test": "active"})

    # After exiting context, subscription should be closed
    with pytest.raises(RuntimeError, match="Cannot send message on closed subscription"):
        await subscription.send_message({"test": "closed"})

    await gateway.close()
