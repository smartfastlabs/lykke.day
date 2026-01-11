"""Command to send a push notification."""

from loguru import logger

from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.domain import data_objects, value_objects


class SendPushNotificationHandler:
    """Sends a push notification to a subscription."""

    def __init__(self, web_push_gateway: WebPushGatewayProtocol) -> None:
        """Initialize SendPushNotificationHandler.

        Args:
            web_push_gateway: Web push notification gateway
        """
        self._web_push_gateway = web_push_gateway

    async def run(
        self,
        subscription: data_objects.PushSubscription,
        content: str | dict | value_objects.NotificationPayload,
    ) -> None:
        """Send a push notification.

        Args:
            subscription: The push subscription to send to
            content: The notification content (string, dict, or NotificationPayload)
        """
        logger.info(f"Sending push notification to subscription {subscription.id}")
        await self._web_push_gateway.send_notification(
            subscription=subscription,
            content=content,
        )
        logger.info(f"Successfully sent push notification to subscription {subscription.id}")
