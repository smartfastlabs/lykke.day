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

from .dependencies.commands.push_subscription import (
    get_create_push_subscription_handler,
    get_delete_push_subscription_handler,
    get_send_push_notification_handler,
    get_update_push_subscription_handler,
)
from .dependencies.queries.push_subscription import (
    get_list_push_subscriptions_handler,
    get_push_subscription_handler,
)
from .dependencies.user import get_current_user

router = APIRouter()


@router.post(
    "/subscriptions/", response_model=PagedResponseSchema[PushSubscriptionSchema]
)
async def search_subscriptions(
    list_push_subscriptions_handler: Annotated[
        SearchPushSubscriptionsHandler, Depends(get_list_push_subscriptions_handler)
    ],
    query: QuerySchema[value_objects.PushSubscriptionQuery],
) -> PagedResponseSchema[PushSubscriptionSchema]:
    """Search push subscriptions with pagination and optional filters."""
    # Build the search query from the request
    filters = query.filters or value_objects.PushSubscriptionQuery()
    search_query = value_objects.PushSubscriptionQuery(
        limit=query.limit,
        offset=query.offset,
        created_before=filters.created_before,
        created_after=filters.created_after,
        order_by=filters.order_by,
        order_by_desc=filters.order_by_desc,
    )
    result = await list_push_subscriptions_handler.run(search_query=search_query)
    subscription_schemas = [
        map_push_subscription_to_schema(sub) for sub in result.items
    ]
    return PagedResponseSchema(
        items=subscription_schemas,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )


@router.get("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def get_subscription(
    subscription_id: str,
    push_subscription_handler: Annotated[
        GetPushSubscriptionHandler, Depends(get_push_subscription_handler)
    ],
) -> PushSubscriptionSchema:
    result = await push_subscription_handler.run(subscription_id=UUID(subscription_id))
    return map_push_subscription_to_schema(result)


@router.put("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def update_subscription(
    subscription_id: str,
    update_data: PushSubscriptionUpdateSchema,
    update_push_subscription_handler: Annotated[
        UpdatePushSubscriptionHandler, Depends(get_update_push_subscription_handler)
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
        DeletePushSubscriptionHandler, Depends(get_delete_push_subscription_handler)
    ],
) -> None:
    await delete_push_subscription_handler.run(subscription_id=UUID(subscription_id))


@router.post("/subscribe/", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: PushSubscriptionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_push_subscription_handler: Annotated[
        CreatePushSubscriptionHandler, Depends(get_create_push_subscription_handler)
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
