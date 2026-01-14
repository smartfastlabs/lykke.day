"""Unit tests for Redis PubSub gateway."""

import asyncio
import json
from uuid import uuid4

import pytest

from lykke.infrastructure.gateways.redis_pubsub import RedisPubSubGateway


@pytest.mark.asyncio
async def test_publish_to_user_channel() -> None:
    """Test publishing a message to a user-specific channel."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()
    message = {"event": "test", "data": "hello"}

    # Should not raise any errors
    await gateway.publish_to_user_channel(
        user_id=user_id, channel_type="auditlog", message=message
    )

    await gateway.close()


@pytest.mark.asyncio
async def test_subscribe_and_receive_message() -> None:
    """Test subscribing to a channel and receiving a message."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()
    message = {"event": "test", "data": "hello world"}

    # Subscribe to the channel using context manager
    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        # Publish a message to the channel (need small delay for subscription to be ready)
        await asyncio.sleep(0.1)
        await gateway.publish_to_user_channel(
            user_id=user_id, channel_type="auditlog", message=message
        )

        # Receive the message
        received = await subscription.get_message(timeout=2.0)

        assert received is not None
        assert received["event"] == "test"
        assert received["data"] == "hello world"

    await gateway.close()


@pytest.mark.asyncio
async def test_subscribe_timeout() -> None:
    """Test that get_message returns None when timeout occurs."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        # Try to receive a message with short timeout (no message published)
        received = await subscription.get_message(timeout=0.5)

        assert received is None

    await gateway.close()


@pytest.mark.asyncio
async def test_multiple_subscribers() -> None:
    """Test that multiple subscribers can receive the same message."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()
    message = {"event": "broadcast", "data": "multi-subscriber test"}

    # Create two subscriptions for the same channel using context managers
    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as sub1:
        async with gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="auditlog"
        ) as sub2:
            # Wait for subscriptions to be ready
            await asyncio.sleep(0.1)

            # Publish one message
            await gateway.publish_to_user_channel(
                user_id=user_id, channel_type="auditlog", message=message
            )

            # Both subscribers should receive the message
            received1 = await sub1.get_message(timeout=2.0)
            received2 = await sub2.get_message(timeout=2.0)

            assert received1 is not None
            assert received1["event"] == "broadcast"
            assert received2 is not None
            assert received2["event"] == "broadcast"

    await gateway.close()


@pytest.mark.asyncio
async def test_channel_isolation() -> None:
    """Test that messages are isolated to specific user channels."""
    gateway = RedisPubSubGateway()
    user1_id = uuid4()
    user2_id = uuid4()

    async with gateway.subscribe_to_user_channel(
        user_id=user1_id, channel_type="auditlog"
    ) as sub1:
        async with gateway.subscribe_to_user_channel(
            user_id=user2_id, channel_type="auditlog"
        ) as sub2:
            await asyncio.sleep(0.1)

            # Publish message to user1's channel
            message1 = {"event": "user1_event", "data": "for user1"}
            await gateway.publish_to_user_channel(
                user_id=user1_id, channel_type="auditlog", message=message1
            )

            # User1 should receive the message
            received1 = await sub1.get_message(timeout=2.0)
            assert received1 is not None
            assert received1["event"] == "user1_event"

            # User2 should NOT receive the message (timeout)
            received2 = await sub2.get_message(timeout=0.5)
            assert received2 is None

    await gateway.close()


@pytest.mark.asyncio
async def test_get_channel_name() -> None:
    """Test channel name generation."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    channel = gateway._get_channel_name(user_id, "auditlog")

    assert channel == f"auditlog:{user_id}"

    await gateway.close()


@pytest.mark.asyncio
async def test_json_serialization() -> None:
    """Test that messages are properly JSON serialized."""
    gateway = RedisPubSubGateway()
    user_id = uuid4()

    # Complex message with various types
    message = {
        "string": "test",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
    }

    async with gateway.subscribe_to_user_channel(
        user_id=user_id, channel_type="auditlog"
    ) as subscription:
        await asyncio.sleep(0.1)

        await gateway.publish_to_user_channel(
            user_id=user_id, channel_type="auditlog", message=message
        )

        received = await subscription.get_message(timeout=2.0)

        assert received is not None
        assert received == message

    await gateway.close()
