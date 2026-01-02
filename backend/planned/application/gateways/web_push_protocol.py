"""Protocol for web push notification gateway."""

from typing import Protocol

from planned.domain import entities


class WebPushGatewayProtocol(Protocol):
    """Protocol defining the interface for web push notification gateways."""

    async def send_notification(
        self,
        subscription: entities.PushSubscription,
        content: str | dict | entities.NotificationPayload,
    ) -> None:
        """Send a push notification to a subscription.

        Args:
            subscription: The push subscription to send to.
            content: The notification content (string, dict, or NotificationPayload).
        """
        ...

