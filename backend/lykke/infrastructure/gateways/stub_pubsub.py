"""Stub implementation of PubSubGateway for testing and non-broadcasting contexts."""

from typing import Any, Self
from uuid import UUID


class StubPubSubSubscription:
    """Stub implementation of PubSubSubscription that does nothing."""

    async def __aenter__(self) -> Self:
        """Enter the subscription context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the subscription context."""
        pass

    async def get_message(
        self, timeout: float | None = None
    ) -> dict[str, Any] | None:
        """Return None (no messages)."""
        return None

    async def send_message(self, message: dict[str, Any]) -> None:
        """Do nothing."""
        pass

    async def close(self) -> None:
        """Do nothing."""
        pass


class StubPubSubGateway:
    """Stub implementation of PubSubGatewayProtocol that does nothing.

    This is useful for:
    - Tests that don't need pub/sub functionality
    - Background workers that don't need to broadcast events
    - Development environments without Redis
    """

    async def publish_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
        message: dict[str, Any],
    ) -> None:
        """Do nothing (no-op publish)."""
        pass

    def subscribe_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
    ) -> StubPubSubSubscription:
        """Return a stub subscription."""
        return StubPubSubSubscription()

    async def close(self) -> None:
        """Do nothing."""
        pass
