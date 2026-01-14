"""Redis-based implementation of PubSub gateway."""

import json
from typing import Any
from uuid import UUID

from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.application.gateways.pubsub_protocol import (
    PubSubGatewayProtocol,
    PubSubSubscription,
)
from lykke.core.config import settings
from lykke.infrastructure.gateways.redis_pubsub.subscription_context_manager import (
    _SubscriptionContextManager,
)


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
