"""Protocol for pub/sub messaging gateway."""

from typing import Any, Protocol, Self
from uuid import UUID


class PubSubGatewayProtocol(Protocol):
    """Protocol defining the interface for pub/sub messaging gateways.

    Enables publishing messages to user-specific channels that can be
    subscribed to by other processes (e.g., WebSocket handlers).
    """

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
        ...

    def subscribe_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
    ) -> "PubSubSubscription":
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
        ...

    async def append_to_user_stream(
        self,
        user_id: UUID,
        stream_type: str,
        message: dict[str, Any],
        *,
        maxlen: int | None = None,
    ) -> str:
        """Append a message to a user-specific Redis stream.

        Args:
            user_id: The user whose stream to append to
            stream_type: Type of stream (e.g., 'entity-changes')
            message: The message payload to append (must be JSON-serializable)
            maxlen: Optional approximate max length for the stream

        Returns:
            The Redis stream entry ID
        """
        ...

    async def read_user_stream(
        self,
        user_id: UUID,
        stream_type: str,
        last_id: str,
        *,
        count: int | None = None,
        block_ms: int | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Read messages from a user-specific Redis stream.

        Args:
            user_id: The user whose stream to read from
            stream_type: Type of stream (e.g., 'entity-changes')
            last_id: The last seen Redis stream ID
            count: Optional max number of entries to read
            block_ms: Optional block time in milliseconds

        Returns:
            List of (stream_id, payload) tuples
        """
        ...

    async def get_latest_user_stream_entry(
        self, user_id: UUID, stream_type: str
    ) -> tuple[str, dict[str, Any]] | None:
        """Get the latest entry from a user-specific Redis stream."""
        ...

    async def get_oldest_user_stream_entry(
        self, user_id: UUID, stream_type: str
    ) -> tuple[str, dict[str, Any]] | None:
        """Get the oldest entry from a user-specific Redis stream."""
        ...


class PubSubSubscription(Protocol):
    """Protocol for a pub/sub subscription.

    Represents an active subscription to a channel. Can be used as an async
    context manager for automatic cleanup.
    """

    async def __aenter__(self) -> Self:
        """Enter the subscription context."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the subscription context and clean up resources."""
        ...

    async def get_message(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Get the next message from the subscription.

        Args:
            timeout: Optional timeout in seconds. None means wait forever.

        Returns:
            The message payload, or None if timeout occurred
        """
        ...

    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a message to the channel.

        Args:
            message: The message payload to send (must be JSON-serializable)
        """
        ...

    async def close(self) -> None:
        """Close the subscription and clean up resources."""
        ...
