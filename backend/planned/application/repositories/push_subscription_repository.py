"""Protocol for PushSubscriptionRepository."""

from typing import Protocol

from planned.domain.entities import PushSubscription


class PushSubscriptionRepositoryProtocol(Protocol):
    """Protocol defining the interface for push subscription repositories."""

    async def get(self, key: str) -> PushSubscription:
        """Get a push subscription by key."""
        ...

    async def put(self, obj: PushSubscription) -> PushSubscription:
        """Save or update a push subscription."""
        ...

    async def all(self) -> list[PushSubscription]:
        """Get all push subscriptions."""
        ...

