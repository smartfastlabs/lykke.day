"""Redis-based implementation of PubSub gateway."""

import asyncio
import json
from typing import Any, cast
from uuid import UUID

from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.application.gateways.pubsub_protocol import (
    PubSubGatewayProtocol,
    PubSubSubscription,
)
from lykke.core.config import settings


class _SubscriptionContextManager:
    """Internal context manager for subscriptions.
    
    This handles the async initialization required for subscribing.
    Implements the PubSubSubscription protocol.
    """

    def __init__(
        self, gateway: "RedisPubSubGateway", user_id: UUID, channel_type: str
    ) -> None:
        """Initialize the context manager.

        Args:
            gateway: The Redis PubSub gateway
            user_id: The user ID
            channel_type: The channel type
        """
        self._gateway = gateway
        self._user_id = user_id
        self._channel_type = channel_type
        self._subscription: RedisSubscription | None = None

    async def __aenter__(self) -> "_SubscriptionContextManager":
        """Enter the context and create the subscription."""
        redis = await self._gateway._get_redis()
        channel = self._gateway._get_channel_name(self._user_id, self._channel_type)

        try:
            # Create a new PubSub instance for this subscription
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel)

            logger.debug(f"Subscribed to channel {channel}")

            self._subscription = RedisSubscription(pubsub, channel, redis)
            return self

        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the context and clean up the subscription."""
        if self._subscription is not None:
            await self._subscription.close()

    async def get_message(
        self, timeout: float | None = None
    ) -> dict[str, Any] | None:
        """Get the next message from the subscription.

        This method is included for protocol compatibility but should not be
        called directly. Use the context manager instead.
        """
        if self._subscription is None:
            raise RuntimeError(
                "Cannot get message before entering context. "
                "Use 'async with subscribe_to_user_channel() as sub:'"
            )
        return await self._subscription.get_message(timeout)

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a message to the channel.

        This method is included for protocol compatibility but should not be
        called directly. Use the context manager instead.
        """
        if self._subscription is None:
            raise RuntimeError(
                "Cannot send message before entering context. "
                "Use 'async with subscribe_to_user_channel() as sub:'"
            )
        await self._subscription.send_message(message)

    async def close(self) -> None:
        """Close the subscription.

        This method is included for protocol compatibility but should not be
        called directly when using the context manager.
        """
        if self._subscription is not None:
            await self._subscription.close()


class RedisSubscription:
    """Redis implementation of PubSubSubscription protocol.
    
    Can be used as an async context manager for automatic cleanup.
    """

    def __init__(
        self,
        pubsub: aioredis.client.PubSub,
        channel: str,
        redis: aioredis.Redis,
    ) -> None:
        """Initialize the subscription.

        Args:
            pubsub: The Redis PubSub object
            channel: The channel name
            redis: The Redis client for publishing
        """
        self._pubsub = pubsub
        self._channel = channel
        self._redis = redis
        self._closed = False

    async def __aenter__(self) -> "RedisSubscription":
        """Enter the subscription context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the subscription context and clean up resources."""
        await self.close()

    async def get_message(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Get the next message from the subscription.

        Args:
            timeout: Optional timeout in seconds. None means wait forever.

        Returns:
            The message payload, or None if timeout occurred or subscription closed
        """
        if self._closed:
            return None

        try:
            # Use asyncio.wait_for for timeout if specified
            if timeout is not None:
                # Wait for a message with timeout
                # The get_message itself will loop until it gets a real message
                async def _wait_for_message() -> dict[str, Any] | None:
                    while True:
                        message = await self._pubsub.get_message(
                            ignore_subscribe_messages=True, timeout=0.1
                        )
                        if message and message["type"] == "message":
                            # Decode and parse the JSON message
                            data = message["data"]
                            if isinstance(data, bytes):
                                data = data.decode("utf-8")
                            return cast(dict[str, Any], json.loads(data))

                return await asyncio.wait_for(_wait_for_message(), timeout=timeout)
            else:
                # Wait indefinitely for a message
                while True:
                    message = await self._pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message["type"] == "message":
                        # Decode and parse the JSON message
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        return cast(dict[str, Any], json.loads(data))

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(
                f"Error receiving message from Redis channel {self._channel}: {e}"
            )
            return None

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a message to the channel.

        Args:
            message: The message payload to send (must be JSON-serializable)
        """
        if self._closed:
            raise RuntimeError("Cannot send message on closed subscription")

        try:
            # Serialize message to JSON
            message_json = json.dumps(message)

            # Publish to Redis channel
            subscribers = await self._redis.publish(self._channel, message_json)

            logger.debug(
                f"Sent message to channel {self._channel} "
                f"(reached {subscribers} subscribers)"
            )

        except Exception as e:
            logger.error(f"Failed to send message to channel {self._channel}: {e}")
            raise

    async def close(self) -> None:
        """Close the subscription and clean up resources."""
        if not self._closed:
            self._closed = True
            try:
                await self._pubsub.unsubscribe(self._channel)
                await self._pubsub.close()
            except Exception as e:
                logger.error(f"Error closing Redis subscription for {self._channel}: {e}")


class RedisPubSubGateway(PubSubGatewayProtocol):
    """Redis-based implementation of pub/sub gateway.

    Uses Redis Pub/Sub for real-time message broadcasting to user-specific channels.
    """

    def __init__(self) -> None:
        """Initialize the Redis PubSub gateway."""
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create the Redis client.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # We'll handle decoding manually
            )
        return self._redis

    def _get_channel_name(self, user_id: UUID, channel_type: str) -> str:
        """Generate a channel name for a user and channel type.

        Args:
            user_id: The user ID
            channel_type: The channel type (e.g., 'auditlog')

        Returns:
            The channel name (e.g., 'auditlog:user-id')
        """
        return f"{channel_type}:{user_id}"

    async def publish_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
        message: dict[str, Any],
    ) -> None:
        """Publish a message to a user-specific channel.

        Args:
            user_id: The user whose channel to publish to
            channel_type: Type of channel (e.g., 'auditlog', 'notification')
            message: The message payload to publish (must be JSON-serializable)
        """
        redis = await self._get_redis()
        channel = self._get_channel_name(user_id, channel_type)

        try:
            # Serialize message to JSON
            message_json = json.dumps(message)

            # Publish to Redis channel
            subscribers = await redis.publish(channel, message_json)

            logger.debug(
                f"Published message to channel {channel} "
                f"(reached {subscribers} subscribers)"
            )

        except Exception as e:
            logger.error(f"Failed to publish message to channel {channel}: {e}")
            raise

    def subscribe_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
    ) -> PubSubSubscription:
        """Subscribe to a user-specific channel.

        Args:
            user_id: The user whose channel to subscribe to
            channel_type: Type of channel (e.g., 'auditlog', 'notification')

        Returns:
            A subscription context manager that can be used to receive and send messages
            
        Usage:
            async with gateway.subscribe_to_user_channel(user_id, "auditlog") as sub:
                message = await sub.get_message()
                await sub.send_message({"response": "ok"})
        """
        return _SubscriptionContextManager(self, user_id, channel_type)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
