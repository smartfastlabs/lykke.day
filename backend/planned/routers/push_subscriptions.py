from fastapi import APIRouter, BackgroundTasks

from planned import gateways, objects
from planned.repositories import push_subscription_repo

router = APIRouter()


class Keys(objects.BaseObject):
    p256dh: str
    auth: str


class SubscriptionRequest(objects.BaseObject):
    endpoint: str
    keys: Keys


@router.post("/subscribe")
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
) -> objects.PushSubscription:
    result: objects.PushSubscription = await push_subscription_repo.put(
        objects.PushSubscription(
            endpoint=request.endpoint,
            p256dh=request.keys.p256dh,
            auth=request.keys.auth,
        )
    )

    background_tasks.add_task(
        gateways.web_push.send_notification,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )

    return result
