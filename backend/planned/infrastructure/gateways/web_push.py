import json

import aiohttp
from webpush import WebPush, WebPushMessage, WebPushSubscription  # type: ignore

from planned.application.gateways.web_push_protocol import WebPushGatewayProtocol
from planned.core.config import settings
from planned.core.exceptions import PushNotificationError
from planned.domain import value_objects
from planned.infrastructure import data_objects

wp = WebPush(
    public_key=settings.VAPID_PUBLIC_KEY.encode("utf-8"),
    private_key=settings.VAPID_SECRET_KEY.encode("utf-8"),
    subscriber="todd@smartfast.com",
)


async def send_notification(
    subscription: data_objects.PushSubscription,
    content: str | dict | value_objects.NotificationPayload,
) -> None:
    from planned.core.utils.serialization import dataclass_to_json_dict

    if isinstance(content, value_objects.NotificationPayload):
        content_dict = dataclass_to_json_dict(content)
        # Filter out None values for JSON
        filtered_content = {
            k: v for k, v in content_dict.items() if v is not None
        }
        content = json.dumps(filtered_content)
    elif isinstance(content, dict):
        content = json.dumps(content)

    message: WebPushMessage = wp.get(
        content,
        WebPushSubscription(
            endpoint=subscription.endpoint,
            keys={
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        ),
    )

    async with aiohttp.ClientSession() as session:
        response = await session.post(
            url=subscription.endpoint,
            data=message.encrypted,
            headers=message.headers,
        )
        if not response.ok:
            raise PushNotificationError(
                f"Failed to send push notification: {response.status} {response.reason}",
            )


class WebPushGateway(WebPushGatewayProtocol):
    """Gateway that implements WebPushGatewayProtocol using infrastructure implementation."""

    async def send_notification(
        self,
        subscription: data_objects.PushSubscription,
        content: str | dict | value_objects.NotificationPayload,
    ) -> None:
        """Send a push notification to a subscription."""
        await send_notification(
            subscription=subscription,
            content=content,
        )
