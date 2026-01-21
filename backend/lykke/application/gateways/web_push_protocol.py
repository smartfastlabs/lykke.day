"""Protocol for web push notification gateway."""

from typing import Protocol

from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity


class WebPushGatewayProtocol(Protocol):
    """Protocol defining the interface for web push notification gateways."""

    async def send_notification(
        self,
        subscription: PushSubscriptionEntity,
        content: str | dict | value_objects.NotificationPayload,
    ) -> None:
        """Send a push notification to a subscription.

        Args:
            subscription: The push subscription to send to.
            content: The notification content (string, dict, or NotificationPayload).
        """
        ...

