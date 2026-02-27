from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from lykke.application.commands.push_subscription import (
    CreatePushSubscriptionCommand,
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionCommand,
    DeletePushSubscriptionHandler,
    SendPushNotificationCommand,
    SendPushNotificationHandler,
    UpdatePushSubscriptionCommand,
    UpdatePushSubscriptionHandler,
)
from lykke.application.queries.push_subscription import (
    GetPushSubscriptionHandler,
    GetPushSubscriptionQuery,
    SearchPushSubscriptionsHandler,
    SearchPushSubscriptionsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import PushSubscriptionEntity, UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    PushSubscriptionCreateSchema,
    PushSubscriptionSchema,
    PushSubscriptionUpdateSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_push_subscription_to_schema

from .dependencies.factories import create_command_handler, create_query_handler
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.post(
    "/subscriptions/", response_model=PagedResponseSchema[PushSubscriptionSchema]
)
async def search_subscriptions(
    query: QuerySchema[value_objects.PushSubscriptionQuery],
    handler: Annotated[
        SearchPushSubscriptionsHandler,
        Depends(create_query_handler(SearchPushSubscriptionsHandler)),
    ],
) -> PagedResponseSchema[PushSubscriptionSchema]:
    """Search push subscriptions with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.PushSubscriptionQuery)
    result = await handler.handle(
        SearchPushSubscriptionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_push_subscription_to_schema)


@router.get("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def get_subscription(
    subscription_id: str,
    handler: Annotated[
        GetPushSubscriptionHandler,
        Depends(create_query_handler(GetPushSubscriptionHandler)),
    ],
) -> PushSubscriptionSchema:
    result = await handler.handle(
        GetPushSubscriptionQuery(push_subscription_id=UUID(subscription_id))
    )
    return map_push_subscription_to_schema(result)


@router.put("/subscriptions/{subscription_id}", response_model=PushSubscriptionSchema)
async def update_subscription(
    subscription_id: str,
    update_data: PushSubscriptionUpdateSchema,
    handler: Annotated[
        UpdatePushSubscriptionHandler,
        Depends(create_command_handler(UpdatePushSubscriptionHandler)),
    ],
) -> PushSubscriptionSchema:
    update_object = value_objects.PushSubscriptionUpdateObject(
        device_name=update_data.device_name
    )
    result = await handler.handle(
        UpdatePushSubscriptionCommand(
            subscription_id=UUID(subscription_id), update_data=update_object
        )
    )
    return map_push_subscription_to_schema(result)


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    handler: Annotated[
        DeletePushSubscriptionHandler,
        Depends(create_command_handler(DeletePushSubscriptionHandler)),
    ],
) -> None:
    await handler.handle(
        DeletePushSubscriptionCommand(subscription_id=UUID(subscription_id))
    )


@router.post("/subscribe/", response_model=PushSubscriptionSchema)
async def subscribe(
    background_tasks: BackgroundTasks,
    request: PushSubscriptionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    create_handler: Annotated[
        CreatePushSubscriptionHandler,
        Depends(create_command_handler(CreatePushSubscriptionHandler)),
    ],
    send_handler: Annotated[
        SendPushNotificationHandler,
        Depends(create_command_handler(SendPushNotificationHandler)),
    ],
) -> PushSubscriptionSchema:
    subscription = PushSubscriptionEntity(
        user_id=user.id,
        device_name=request.device_name,
        endpoint=request.endpoint,
        p256dh=request.keys.p256dh,
        auth=request.keys.auth,
    )
    result = await create_handler.handle(
        CreatePushSubscriptionCommand(subscription=subscription)
    )

    background_tasks.add_task(
        send_handler.handle,
        SendPushNotificationCommand(
            subscriptions=[result],
            content={
                "title": "Notifications Enabled!",
                "body": "Look at that a notification ;)",
            },
        ),
    )

    return map_push_subscription_to_schema(result)


@router.post("/test-push/")
async def send_test_push(
    background_tasks: BackgroundTasks,
    search_handler: Annotated[
        SearchPushSubscriptionsHandler,
        Depends(create_query_handler(SearchPushSubscriptionsHandler)),
    ],
    send_handler: Annotated[
        SendPushNotificationHandler,
        Depends(create_command_handler(SendPushNotificationHandler)),
    ],
) -> dict[str, int]:
    """Send a test push notification to all user's subscribed devices.

    Returns:
        A dict with the count of devices that will receive the notification.
    """
    result = await search_handler.handle(SearchPushSubscriptionsQuery())

    if result.items:
        background_tasks.add_task(
            send_handler.handle,
            SendPushNotificationCommand(
                subscriptions=result.items,
                content={
                    "title": "Test Notification",
                    "body": "This is a test push notification from Planned.day!",
                },
            ),
        )

    return {"device_count": len(result.items)}
