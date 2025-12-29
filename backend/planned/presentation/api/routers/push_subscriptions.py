from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from planned.application.repositories import PushSubscriptionRepositoryProtocol
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.value_objects.base import BaseRequestObject, BaseValueObject
from planned.infrastructure.gateways import web_push

from .dependencies.repositories import get_push_subscription_repo
from .dependencies.user import get_current_user

router = APIRouter()


class Keys(BaseValueObject):
    p256dh: str
    auth: str


class SubscriptionRequest(BaseRequestObject):
    device_name: str
    endpoint: str
    keys: Keys


@router.get("/subscriptions")
async def list_subscriptions(
    push_subscription_repo: Annotated[PushSubscriptionRepositoryProtocol, Depends(
        get_push_subscription_repo
    )],
) -> list[objects.PushSubscription]:
    return await push_subscription_repo.all()


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    push_subscription_repo: Annotated[PushSubscriptionRepositoryProtocol, Depends(
        get_push_subscription_repo
    )],
) -> None:
    await push_subscription_repo.delete(UUID(subscription_id))


@router.post("/subscribe")
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
    user: Annotated[User, Depends(get_current_user)],
    push_subscription_repo: Annotated[PushSubscriptionRepositoryProtocol, Depends(
        get_push_subscription_repo
    )],
) -> objects.PushSubscription:
    result: objects.PushSubscription = await push_subscription_repo.put(
        objects.PushSubscription(
            user_uuid=user.uuid,
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
