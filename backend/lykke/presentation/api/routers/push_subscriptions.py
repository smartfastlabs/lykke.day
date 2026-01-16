from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from lykke.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
    SendPushNotificationHandler,
    UpdatePushSubscriptionHandler,
)
from lykke.application.queries.push_subscription import (
    GetPushSubscriptionHandler,
    SearchPushSubscriptionsHandler,
)
from lykke.domain import data_objects, value_objects
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    PushSubscriptionCreateSchema,
    PushSubscriptionSchema,
    PushSubscriptionUpdateSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.commands.push_subscription import get_send_push_notification_handler
from .dependencies.factories import get_command_handler, get_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.post(
    "/subscriptions/", response_model=PagedResponseSchema[PushSubscriptionSchema]
)
async def search_subscriptions(
    list_push_subscriptions_handler: Annotated[
        SearchPushSubscriptionsHandler, Depends(get_query_handler(SearchPushSubscriptionsHandler))
    ],
    query: QuerySchema[value_objects.PushSubscriptionQuery],
) -> PagedResponseSchema[PushSubscriptionSchema]:
    """Search push subscriptions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.PushSubscriptionQuery)
    result = await list_push_subscriptions_handler.run(search_query=search_query)
    return create_paged_response(result, map_push_subscription_to_schema)


@router.get("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def get_subscription(
    subscription_id: str,
    push_subscription_handler: Annotated[
        GetPushSubscriptionHandler, Depends(get_query_handler(GetPushSubscriptionHandler))
    ],
) -> PushSubscriptionSchema:
    result = await push_subscription_handler.run(subscription_id=UUID(subscription_id))
    return map_push_subscription_to_schema(result)


@router.put("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def update_subscription(
    subscription_id: str,
    update_data: PushSubscriptionUpdateSchema,
    update_push_subscription_handler: Annotated[
        UpdatePushSubscriptionHandler, Depends(get_command_handler(UpdatePushSubscriptionHandler))
    ],
) -> PushSubscriptionSchema:
    update_object = value_objects.PushSubscriptionUpdateObject(
        device_name=update_data.device_name
    )
    result = await update_push_subscription_handler.run(
        subscription_id=UUID(subscription_id), update_data=update_object
    )
    return map_push_subscription_to_schema(result)


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    delete_push_subscription_handler: Annotated[
        DeletePushSubscriptionHandler, Depends(get_command_handler(DeletePushSubscriptionHandler))
    ],
) -> None:
    await delete_push_subscription_handler.run(subscription_id=UUID(subscription_id))


@router.post("/subscribe/", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: PushSubscriptionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_push_subscription_handler: Annotated[
        CreatePushSubscriptionHandler, Depends(get_command_handler(CreatePushSubscriptionHandler))
    ],
    send_push_notification_handler: Annotated[
        SendPushNotificationHandler, Depends(get_send_push_notification_handler)
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
        send_push_notification_handler.run,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )

    return map_push_subscription_to_schema(result)
