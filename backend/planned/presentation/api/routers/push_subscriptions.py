from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from planned.application.commands import CreateEntityHandler, DeleteEntityHandler
from planned.application.queries import ListEntitiesHandler
from planned.domain import value_objects
from planned.domain.entities import UserEntity
from planned.infrastructure import data_objects
from planned.infrastructure.gateways import web_push
from planned.presentation.api.schemas import PushSubscriptionSchema
from planned.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.services import (
    get_create_entity_handler,
    get_delete_entity_handler,
    get_list_entities_handler,
)
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
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[ListEntitiesHandler, Depends(get_list_entities_handler)],
) -> list[PushSubscriptionSchema]:
    result: (
        list[data_objects.PushSubscription]
        | value_objects.PagedQueryResponse[data_objects.PushSubscription]
    ) = await handler.list_entities(
        user_id=user.id,
        repository_name="push_subscriptions",
        paginate=False,
    )
    subscriptions = result if isinstance(result, list) else result.items
    return [map_push_subscription_to_schema(sub) for sub in subscriptions]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[DeleteEntityHandler, Depends(get_delete_entity_handler)],
) -> None:
    await handler.delete_entity(
        user_id=user.id,
        repository_name="push_subscriptions",
        entity_id=UUID(subscription_id),
    )


@router.post("/subscribe", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[CreateEntityHandler, Depends(get_create_entity_handler)],
) -> PushSubscriptionSchema:
    subscription = data_objects.PushSubscription(
        user_id=user.id,
        device_name=request.device_name,
        endpoint=request.endpoint,
        p256dh=request.keys.p256dh,
        auth=request.keys.auth,
    )
    result: data_objects.PushSubscription = await handler.create_entity(
        user_id=user.id,
        repository_name="push_subscriptions",
        entity=subscription,
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
