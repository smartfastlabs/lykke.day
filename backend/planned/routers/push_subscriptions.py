from fastapi import APIRouter, BackgroundTasks

from planned import objects
from planned.gateways import web_push
from planned.repositories import push_subscription_repo

router = APIRouter()


class Keys(objects.BaseObject):
    p256dh: str
    auth: str


class SubscriptionRequest(objects.BaseObject):
    device_name: str
    endpoint: str
    keys: Keys


@router.get("/subscriptions")
async def list_subscriptions() -> list[objects.PushSubscription]:
    return await push_subscription_repo.all()


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str) -> None:
    await push_subscription_repo.delete(subscription_id)


@router.post("/subscribe")
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
) -> objects.PushSubscription:
    result: objects.PushSubscription = await push_subscription_repo.put(
        objects.PushSubscription(
            device_name=request.device_name,
            endpoint=request.endpoint,
            p256dh=request.keys.p256dh,
            auth=request.keys.auth,
        )
    )

    background_tasks.add_task(
        web_push.send_notification,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )

    return result
