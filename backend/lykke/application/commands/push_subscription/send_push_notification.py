"""Command to send a push notification."""

from dataclasses import dataclass

from loguru import logger

from lykke.application.commands.base import Command
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity


@dataclass(frozen=True)
class SendPushNotificationCommand(Command):
    """Command to send a push notification."""

    subscription: PushSubscriptionEntity
    content: str | dict | value_objects.NotificationPayload


class SendPushNotificationHandler:
    """Sends a push notification to a subscription."""

    def __init__(self, web_push_gateway: WebPushGatewayProtocol) -> None:
        """Initialize SendPushNotificationHandler.

        Args:
            web_push_gateway: Web push notification gateway
        """
        self._web_push_gateway = web_push_gateway

    async def handle(self, command: SendPushNotificationCommand) -> None:
        """Send a push notification.

        Args:
            command: The command containing the subscription and content
        """
        logger.info(f"Sending push notification to subscription {command.subscription.id}")
        await self._web_push_gateway.send_notification(
            subscription=command.subscription,
            content=command.content,
        )
        logger.info(f"Successfully sent push notification to subscription {command.subscription.id}")
