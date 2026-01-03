from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from planned.application.commands import CreateEntityCommand, DeleteEntityCommand
from planned.application.mediator import Mediator
from planned.application.queries import ListEntitiesQuery
from planned.domain import value_objects
from planned.domain.entities import UserEntity
from planned.infrastructure import data_objects
from planned.infrastructure.gateways import web_push
from planned.presentation.api.schemas import PushSubscriptionSchema
from planned.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.services import get_mediator
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
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> list[PushSubscriptionSchema]:
    query = ListEntitiesQuery[data_objects.PushSubscription](
        user_id=user.id,
        repository_name="push_subscriptions",
        paginate=False,
    )
    result = await mediator.query(query)
    subscriptions = result if isinstance(result, list) else result.items
    return [map_push_subscription_to_schema(sub) for sub in subscriptions]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> None:
    command = DeleteEntityCommand(
        user_id=user.id,
        repository_name="push_subscriptions",
        entity_id=UUID(subscription_id),
    )
    await mediator.execute(command)


@router.post("/subscribe", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: SubscriptionRequest,
    user: Annotated[UserEntity, Depends(get_current_user)],
    mediator: Annotated[Mediator, Depends(get_mediator)],
) -> PushSubscriptionSchema:
    subscription = data_objects.PushSubscription(
        user_id=user.id,
        device_name=request.device_name,
        endpoint=request.endpoint,
        p256dh=request.keys.p256dh,
        auth=request.keys.auth,
    )
    command = CreateEntityCommand[data_objects.PushSubscription](
        user_id=user.id,
        repository_name="push_subscriptions",
        entity=subscription,
    )
    result = await mediator.execute(command)

    background_tasks.add_task(
        web_push.send_notification,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )

    return map_push_subscription_to_schema(result)
