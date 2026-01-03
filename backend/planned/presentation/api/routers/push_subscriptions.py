from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from planned.application.repositories import PushSubscriptionRepositoryProtocol
from planned.domain import value_objects
from planned.domain.entities import UserEntity
from planned.infrastructure import data_objects
from planned.infrastructure.gateways import web_push
from planned.presentation.api.schemas import PushSubscriptionSchema
from planned.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.repositories import get_push_subscription_repo
from .dependencies.user import get_current_user

router = APIRouter()


class Keys(value_objects.BaseValueObject):
    p256dh: str
    auth: str


class SubscriptionRequest(value_objects.BaseRequestObject):
    device_name: str
    endpoint: str
    keys: Keys


@router.get("/subscriptions", response_model=list[PushSubscriptionSchema])
async def list_subscriptions(
    push_subscription_repo: Annotated[
        PushSubscriptionRepositoryProtocol, Depends(get_push_subscription_repo)
    ],
) -> list[PushSubscriptionSchema]:
    subscriptions = await push_subscription_repo.all()
    return [map_push_subscription_to_schema(sub) for sub in subscriptions]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    push_subscription_repo: Annotated[
        PushSubscriptionRepositoryProtocol, Depends(get_push_subscription_repo)
    ],
) -> None:
    await push_subscription_repo.delete(UUID(subscription_id))


@router.post("/subscribe", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    push_subscription_repo: Annotated[
        PushSubscriptionRepositoryProtocol, Depends(get_push_subscription_repo)
    ],
) -> PushSubscriptionSchema:
    result: data_objects.PushSubscription = await push_subscription_repo.put(
        data_objects.PushSubscription(
            user_id=user.id,
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

    return map_push_subscription_to_schema(result)
