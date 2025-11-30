import json

import aiohttp
from webpush import WebPush, WebPushMessage, WebPushSubscription  # type: ignore

from planned import exceptions, objects, settings

wp = WebPush(
    public_key=settings.VAPID_PUBLIC_KEY.encode("utf-8"),
    private_key=settings.VAPID_SECRET_KEY.encode("utf-8"),
    subscriber="todd@smartfast.com",
)


async def send_notification(
    subscription: objects.PushSubscription,
    content: str | dict,
) -> None:
    if isinstance(content, dict):
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
            raise exceptions.PushNotificationError(
                f"Failed to send push notification: {response.status} {response.reason}",
                504,
            )
