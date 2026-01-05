from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from planned.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
)
from planned.application.queries.push_subscription import SearchPushSubscriptionsHandler
from planned.domain import value_objects
from planned.domain.entities import UserEntity
from planned.infrastructure import data_objects
from planned.infrastructure.gateways import web_push
from planned.presentation.api.schemas import PushSubscriptionSchema
from planned.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.commands.push_subscription import (
    get_create_push_subscription_handler,
    get_delete_push_subscription_handler,
)
from .dependencies.queries.push_subscription import get_list_push_subscriptions_handler
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
    list_push_subscriptions_handler: Annotated[
        SearchPushSubscriptionsHandler, Depends(get_list_push_subscriptions_handler)
    ],
) -> list[PushSubscriptionSchema]:
    result = await list_push_subscriptions_handler.run()
    return [map_push_subscription_to_schema(sub) for sub in result.items]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    delete_push_subscription_handler: Annotated[
        DeletePushSubscriptionHandler, Depends(get_delete_push_subscription_handler)
    ],
) -> None:
    await delete_push_subscription_handler.run(subscription_id=UUID(subscription_id))


@router.post("/subscribe", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_push_subscription_handler: Annotated[
        CreatePushSubscriptionHandler, Depends(get_create_push_subscription_handler)
    ],
) -> PushSubscriptionSchema:
    subscription = data_objects.PushSubscription(
        user_id=user.id,
        device_name=request.device_name,
        endpoint=request.endpoint,
        p256dh=request.keys.p256dh,
        auth=request.keys.auth,
    )
    result = await create_push_subscription_handler.run(subscription=subscription)

    background_tasks.add_task(
        web_push.send_notification,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )

    return map_push_subscription_to_schema(result)
