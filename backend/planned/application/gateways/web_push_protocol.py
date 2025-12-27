"""Protocol for web push notification gateway."""

from typing import Protocol

from planned.domain.entities import NotificationPayload, PushSubscription


class WebPushGatewayProtocol(Protocol):
    """Protocol defining the interface for web push notification gateways."""

    async def send_notification(
        self,
        subscription: PushSubscription,
        content: str | dict | NotificationPayload,
    ) -> None:
        """Send a push notification to a subscription.

        Args:
            subscription: The push subscription to send to.
            content: The notification content (string, dict, or NotificationPayload).
        """
        ...

