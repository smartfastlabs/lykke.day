"""PushSubscription command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.push_subscription import SendPushNotificationHandler
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.infrastructure.gateways import WebPushGateway


def get_web_push_gateway() -> WebPushGatewayProtocol:
    """Get an instance of WebPushGateway."""
    return WebPushGateway()


def get_send_push_notification_handler(
    web_push_gateway: Annotated[
        WebPushGatewayProtocol, Depends(get_web_push_gateway)
    ],
) -> SendPushNotificationHandler:
    """Get a SendPushNotificationHandler instance."""
    return SendPushNotificationHandler(web_push_gateway)

