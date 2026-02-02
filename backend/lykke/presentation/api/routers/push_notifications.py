"""Router for PushNotification read operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lykke.application.queries.push_notification import (
    GetPushNotificationContextHandler,
    GetPushNotificationContextQuery,
    GetPushNotificationHandler,
    GetPushNotificationQuery,
    SearchPushNotificationsHandler,
    SearchPushNotificationsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    PushNotificationContextSchema,
    PushNotificationSchema,
    QuerySchema,
)
from lykke.presentation.api.schemas.mappers import (
    map_push_notification_context_to_schema,
    map_push_notification_to_schema,
)
from lykke.presentation.handler_factory import QueryHandlerFactory

from .dependencies.factories import query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.post("/", response_model=PagedResponseSchema[PushNotificationSchema])
async def search_push_notifications(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.PushNotificationQuery],
) -> PagedResponseSchema[PushNotificationSchema]:
    """Search push notifications with pagination and optional filters."""
    handler = query_factory.create(SearchPushNotificationsHandler)
    search_query = build_search_query(query, value_objects.PushNotificationQuery)
    result = await handler.handle(SearchPushNotificationsQuery(search_query=search_query))
    return create_paged_response(result, map_push_notification_to_schema)


@router.get("/{notification_id}", response_model=PushNotificationSchema)
async def get_push_notification(
    notification_id: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> PushNotificationSchema:
    """Get a specific push notification by ID."""
    handler = query_factory.create(GetPushNotificationHandler)
    notification = await handler.handle(
        GetPushNotificationQuery(push_notification_id=notification_id)
    )
    return map_push_notification_to_schema(notification)


@router.get(
    "/{notification_id}/context", response_model=PushNotificationContextSchema
)
async def get_push_notification_context(
    notification_id: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> PushNotificationContextSchema:
    """Get a push notification context by ID."""
    handler = query_factory.create(GetPushNotificationContextHandler)
    context = await handler.handle(
        GetPushNotificationContextQuery(push_notification_id=notification_id)
    )
    return map_push_notification_context_to_schema(
        context, user_timezone=user.settings.timezone
    )
