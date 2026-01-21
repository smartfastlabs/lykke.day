"""Internal context manager for Redis subscriptions."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from loguru import logger

from lykke.infrastructure.gateways.redis_pubsub.subscription import RedisSubscription

if TYPE_CHECKING:
    from lykke.infrastructure.gateways.redis_pubsub.gateway import RedisPubSubGateway


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
