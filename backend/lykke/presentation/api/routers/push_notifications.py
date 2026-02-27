"""Router for PushNotification read operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.queries.push_notification import (
    GetPushNotificationHandler,
    GetPushNotificationQuery,
    SearchPushNotificationsHandler,
    SearchPushNotificationsQuery,
)
from lykke.domain import value_objects
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    PushNotificationSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import map_push_notification_to_schema

from .dependencies.factories import create_query_handler
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.post("/", response_model=PagedResponseSchema[PushNotificationSchema])
async def search_push_notifications(
    query: QuerySchema[value_objects.PushNotificationQuery],
    handler: Annotated[
        SearchPushNotificationsHandler,
        Depends(create_query_handler(SearchPushNotificationsHandler)),
    ],
) -> PagedResponseSchema[PushNotificationSchema]:
    """Search push notifications with pagination and optional filters."""
    search_query = build_search_query(query, value_objects.PushNotificationQuery)
    result = await handler.handle(SearchPushNotificationsQuery(search_query=search_query))
    return create_paged_response(result, map_push_notification_to_schema)


@router.get("/{notification_id}", response_model=PushNotificationSchema)
async def get_push_notification(
    notification_id: UUID,
    handler: Annotated[
        GetPushNotificationHandler,
        Depends(create_query_handler(GetPushNotificationHandler)),
    ],
) -> PushNotificationSchema:
    """Get a specific push notification by ID."""
    notification = await handler.handle(
        GetPushNotificationQuery(push_notification_id=notification_id)
    )
    return map_push_notification_to_schema(notification)

