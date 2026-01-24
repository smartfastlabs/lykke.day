"""Redis subscription implementation."""

import asyncio
import json
from typing import Any, cast

from loguru import logger
from redis import asyncio as aioredis  # type: ignore


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
            # Get the current event loop to ensure we use the correct one
            asyncio.get_event_loop()

            # Use asyncio.wait_for for timeout if specified
            if timeout is not None:
                # Wait for a message with timeout
                # The get_message itself will loop until it gets a real message
                async def _wait_for_message() -> dict[str, Any] | None:
                    while True:
                        # Ensure we're using the current event loop
                        message = await self._pubsub.get_message(
                            ignore_subscribe_messages=True, timeout=0.1
                        )
                        if message and message["type"] == "message":
                            # Decode and parse the JSON message
                            data = message["data"]
                            if isinstance(data, bytes):
                                data = data.decode("utf-8")
                            return cast("dict[str, Any]", json.loads(data))

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
                        return cast("dict[str, Any]", json.loads(data))

        except TimeoutError:
            return None
        except RuntimeError as e:
            # Handle event loop errors gracefully in test contexts
            if "attached to a different loop" in str(e):
                logger.warning(
                    f"Event loop mismatch for Redis channel {self._channel}, "
                    "this can happen in test contexts with TestClient"
                )
                return None
            logger.error(
                f"Runtime error receiving message from Redis channel {self._channel}: {e}"
            )
            # Mark as closed so we don't keep trying on a broken connection
            self._closed = True
            raise
        except Exception as e:
            error_str = str(e).lower()
            # Check for connection-related errors that indicate the connection is broken
            if any(
                keyword in error_str
                for keyword in ["closed", "connection", "disconnect"]
            ):
                logger.error(f"Connection error for Redis channel {self._channel}: {e}")
                # Mark as closed so we don't keep trying on a broken connection
                self._closed = True
                raise
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
                logger.error(
                    f"Error closing Redis subscription for {self._channel}: {e}"
                )
