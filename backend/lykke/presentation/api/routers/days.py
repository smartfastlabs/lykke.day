"""Routes for day operations."""

import asyncio
import contextlib
import datetime
import json
from datetime import UTC, date, datetime as dt_datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.commands import ScheduleDayHandler, UpdateDayHandler
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import (
    GetDayContextHandler,
    GetIncrementalChangesHandler,
    PreviewDayHandler,
)
from lykke.application.queries.day_template import SearchDayTemplatesHandler
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.audit_log_filtering import is_audit_log_for_today
from lykke.core.utils.audit_log_serialization import deserialize_audit_log
from lykke.core.utils.dates import get_current_date, get_tomorrows_date
from lykke.presentation.api.schemas import (
    DayContextSchema,
    DaySchema,
    DayTemplateSchema,
    DayUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_day_template_to_schema,
    map_day_to_schema,
)
from lykke.presentation.api.schemas.websocket_message import (
    EntityChangeSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketSyncRequestSchema,
    WebSocketSyncResponseSchema,
)

from .dependencies.queries.day_template import get_list_day_templates_handler
from .dependencies.services import (
    day_context_handler,
    day_context_handler_websocket,
    get_pubsub_gateway,
    get_schedule_day_handler,
    get_update_day_handler,
    incremental_changes_handler,
    incremental_changes_handler_websocket,
    preview_day_handler,
)

router = APIRouter()


# ============================================================================
# Day Context Queries
# ============================================================================


@router.get("/today/context", response_model=DayContextSchema)
async def get_context_today(
    handler: Annotated[GetDayContextHandler, Depends(day_context_handler)],
    schedule_handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Get the complete context for today."""
    date = get_current_date()
    try:
        context = await handler.get_day_context(date=date)
    except NotFoundError:
        # If the day does not exist yet, schedule it and return the persisted context
        context = await schedule_handler.schedule_day(date=date)
    return map_day_context_to_schema(context)


@router.get("/tomorrow/context", response_model=DayContextSchema)
async def get_context_tomorrow(
    handler: Annotated[GetDayContextHandler, Depends(day_context_handler)],
    schedule_handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Get the complete context for tomorrow."""
    date = get_tomorrows_date()
    try:
        context = await handler.get_day_context(date=date)
    except NotFoundError:
        context = await schedule_handler.schedule_day(date=date)
    return map_day_context_to_schema(context)


@router.get("/{date}/context", response_model=DayContextSchema)
async def get_context(
    date: datetime.date,
    handler: Annotated[GetDayContextHandler, Depends(day_context_handler)],
    schedule_handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Get the complete context for a specific date."""
    try:
        context = await handler.get_day_context(date=date)
    except NotFoundError:
        context = await schedule_handler.schedule_day(date=date)
    return map_day_context_to_schema(context)


@router.get("/{date}/preview", response_model=DayContextSchema)
async def preview_day(
    date: datetime.date,
    handler: Annotated[PreviewDayHandler, Depends(preview_day_handler)],
    template_id: UUID | None = None,
) -> DayContextSchema:
    """Preview what a day would look like if scheduled."""
    context = await handler.preview_day(date=date, template_id=template_id)
    return map_day_context_to_schema(context)


# ============================================================================
# Day Commands
# ============================================================================


@router.put("/today/schedule", response_model=DayContextSchema)
async def schedule_today(
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
) -> DayContextSchema:
    """Schedule today with tasks from routines."""
    context = await handler.schedule_day(date=get_current_date())
    return map_day_context_to_schema(context)


@router.put("/{date}/schedule", response_model=DayContextSchema)
async def schedule_day(
    date: datetime.date,
    handler: Annotated[ScheduleDayHandler, Depends(get_schedule_day_handler)],
    template_id: UUID | None = None,
) -> DayContextSchema:
    """Schedule a specific day with tasks from routines."""
    context = await handler.schedule_day(date=date, template_id=template_id)
    return map_day_context_to_schema(context)


@router.patch("/{date}", response_model=DaySchema)
async def update_day(
    date: datetime.date,
    update_data: DayUpdateSchema,
    handler: Annotated[UpdateDayHandler, Depends(get_update_day_handler)],
) -> DaySchema:
    """Update a day's status or template."""
    # Convert schema to update object
    from lykke.domain.value_objects import DayUpdateObject
    from lykke.domain.value_objects.alarm import Alarm

    alarm = None
    if update_data.alarm:
        alarm = Alarm(
            name=update_data.alarm.name,
            time=update_data.alarm.time,
            type=update_data.alarm.type,
            description=update_data.alarm.description,
            triggered_at=update_data.alarm.triggered_at,
        )

    update_object = DayUpdateObject(
        alarm=alarm,
        status=update_data.status,
        scheduled_at=update_data.scheduled_at,
        tags=update_data.tags,
        template_id=update_data.template_id,
    )
    day = await handler.update_day(
        date=date,
        update_data=update_object,
    )
    return map_day_to_schema(day)


# ============================================================================
# Templates
# ============================================================================


@router.get("/templates/", response_model=list[DayTemplateSchema])
@router.get("/templates", response_model=list[DayTemplateSchema])
async def get_templates(
    list_day_templates_handler: Annotated[
        SearchDayTemplatesHandler, Depends(get_list_day_templates_handler)
    ],
) -> list[DayTemplateSchema]:
    """Get all available day templates."""
    result = await list_day_templates_handler.run()
    return [map_day_template_to_schema(template) for template in result.items]


# ============================================================================
# WebSocket Endpoint
# ============================================================================


async def send_ws_message(websocket: WebSocket, message: dict[str, Any]) -> None:
    """Send a JSON message over WebSocket.

    Args:
        websocket: The WebSocket connection
        message: Dictionary to send as JSON
    """
    await websocket.send_text(json.dumps(message))


async def send_error(websocket: WebSocket, code: str, message: str) -> None:
    """Send an error message over WebSocket.

    Args:
        websocket: The WebSocket connection
        code: Error code
        message: Error message
    """
    error_schema = WebSocketErrorSchema(code=code, message=message)
    await send_ws_message(websocket, error_schema.model_dump(mode="json"))


@router.websocket("/today/context")
async def days_context_websocket(
    websocket: WebSocket,
    pubsub_gateway: Annotated[
        PubSubGatewayProtocol, Depends(get_pubsub_gateway)
    ],
    day_context_handler: Annotated[
        GetDayContextHandler, Depends(day_context_handler_websocket)
    ],
    incremental_changes_handler_ws: Annotated[
        GetIncrementalChangesHandler,
        Depends(incremental_changes_handler_websocket),
    ],
) -> None:
    """WebSocket endpoint for real-time DayContext sync.

    This endpoint:
    1. Accepts WebSocket connection
    2. Authenticates user
    3. Handles sync_request messages (full context or incremental changes)
    4. Subscribes to user's AuditLog channel for real-time updates
    5. Filters audit log events to only include entities for today

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()

    try:
        # Get user_id from the handler (user was authenticated via dependency)
        user_id = day_context_handler.user_id
        logger.info(f"Days context WebSocket connection established for user {user_id}")

        # Send connection acknowledgment
        ack = WebSocketConnectionAckSchema(user_id=user_id)
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        # Get today's date
        today_date = get_current_date()

        # Subscribe to user's AuditLog channel for real-time updates
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="auditlog"
        ) as auditlog_subscription:
            # Create tasks for handling messages and real-time events
            message_task = asyncio.create_task(
                _handle_client_messages(
                    websocket,
                    day_context_handler,
                    incremental_changes_handler_ws,
                    today_date,
                )
            )
            events_task = asyncio.create_task(
                _handle_realtime_events(
                    websocket,
                    auditlog_subscription,
                    today_date,
                )
            )

            # Wait for either task to complete (or fail)
            done, pending = await asyncio.wait(
                [message_task, events_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    except WebSocketDisconnect:
        logger.info(
            f"Days context WebSocket disconnected for user {user_id if 'user_id' in locals() else 'unknown'}"
        )

    except Exception as e:
        logger.error(f"Days context WebSocket error: {e}")
        try:
            await send_error(
                websocket, "INTERNAL_ERROR", "An unexpected error occurred"
            )
            await websocket.close()
        except Exception:
            # Connection may already be closed
            pass


async def _handle_client_messages(
    websocket: WebSocket,
    get_day_context_handler: GetDayContextHandler,
    get_incremental_changes_handler: GetIncrementalChangesHandler,
    today_date: date,
) -> None:
    """Handle messages from the client (sync requests).

    Args:
        websocket: WebSocket connection
        get_day_context_handler: Handler for getting full day context
        get_incremental_changes_handler: Handler for getting incremental changes
        today: Today's date
    """
    while True:
        try:
            # Receive message from client
            message_text = await websocket.receive_text()
            message_data = json.loads(message_text)

            # Parse sync request
            try:
                sync_request = WebSocketSyncRequestSchema(**message_data)
            except Exception as e:
                logger.warning(f"Invalid sync request: {e}")
                await send_error(websocket, "INVALID_REQUEST", f"Invalid request: {e}")
                continue

            # Handle sync request
            if sync_request.since_timestamp:
                # Incremental sync
                try:
                    since_dt = dt_datetime.fromisoformat(
                        sync_request.since_timestamp.replace("Z", "+00:00")
                    )
                    if since_dt.tzinfo is None:
                        since_dt = since_dt.replace(tzinfo=UTC)
                    else:
                        since_dt = since_dt.astimezone(UTC)

                    (
                        changes,
                        last_timestamp,
                    ) = await get_incremental_changes_handler.get_incremental_changes(
                        since_dt, today_date
                    )

                    response = WebSocketSyncResponseSchema(
                        changes=changes,
                        day_context=None,
                        last_audit_log_timestamp=last_timestamp.isoformat()
                        if last_timestamp
                        else None,
                    )
                except Exception as e:
                    logger.error(f"Error getting incremental changes: {e}")
                    await send_error(
                        websocket,
                        "INTERNAL_ERROR",
                        f"Failed to get incremental changes: {e}",
                    )
                    continue
            else:
                # Full sync
                try:
                    context = await get_day_context_handler.get_day_context(
                        date=today_date
                    )

                    # Get most recent audit log timestamp
                    from lykke.domain import value_objects

                    audit_logs = (
                        await get_incremental_changes_handler.audit_log_ro_repo.search(
                            value_objects.AuditLogQuery()
                        )
                    )
                    last_audit_timestamp: dt_datetime | None = None
                    if audit_logs:
                        sorted_logs = sorted(
                            audit_logs, key=lambda x: x.occurred_at, reverse=True
                        )
                        last_audit_timestamp = sorted_logs[0].occurred_at

                    response = WebSocketSyncResponseSchema(
                        day_context=map_day_context_to_schema(context),
                        changes=None,
                        last_audit_log_timestamp=last_audit_timestamp.isoformat()
                        if last_audit_timestamp
                        else None,
                    )
                except Exception as e:
                    logger.error(f"Error getting day context: {e}")
                    await send_error(
                        websocket, "INTERNAL_ERROR", f"Failed to get day context: {e}"
                    )
                    continue

            # Send response
            await send_ws_message(websocket, response.model_dump(mode="json"))

        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await send_error(
                websocket, "INTERNAL_ERROR", f"Error processing message: {e}"
            )


async def _handle_realtime_events(
    websocket: WebSocket,
    auditlog_subscription: Any,
    today_date: date,
) -> None:
    """Handle real-time audit log events from pubsub and convert to entity changes.

    Args:
        websocket: WebSocket connection
        auditlog_subscription: PubSub subscription for audit logs
        today: Today's date for filtering
    """
    while True:
        try:
            # Wait for AuditLog events from Redis with timeout
            audit_log_message = await auditlog_subscription.get_message(timeout=1.0)

            if audit_log_message:
                try:
                    # Deserialize audit log
                    audit_log_entity = deserialize_audit_log(audit_log_message)

                    # Filter to only include entities for today
                    if not await is_audit_log_for_today(
                        audit_log_entity,
                        today_date,
                    ):
                        # Skip events for other days
                        continue

                    # Convert audit log to entity change (like GetIncrementalChangesHandler does)
                    change_type: Literal["created", "updated", "deleted"] | None = None
                    if (
                        "Created" in audit_log_entity.activity_type
                        or audit_log_entity.activity_type == "EntityCreatedEvent"
                    ):
                        change_type = "created"
                    elif (
                        "Deleted" in audit_log_entity.activity_type
                        or audit_log_entity.activity_type == "EntityDeletedEvent"
                    ):
                        change_type = "deleted"
                    elif (
                        "Updated" in audit_log_entity.activity_type
                        or audit_log_entity.activity_type == "EntityUpdatedEvent"
                    ):
                        change_type = "updated"
                    else:
                        # Skip events we don't know how to handle
                        continue

                    entity_data: dict[str, Any] | None = None

                    # For created/updated, use the entity snapshot from the audit log
                    if change_type in ("created", "updated"):
                        meta = audit_log_entity.meta
                        if isinstance(meta, dict):
                            entity_snapshot = meta.get("entity_data")
                            if isinstance(entity_snapshot, dict):
                                entity_data = entity_snapshot

                    # Create entity change schema
                    entity_change = EntityChangeSchema(
                        change_type=change_type,
                        entity_type=audit_log_entity.entity_type or "unknown",
                        entity_id=audit_log_entity.entity_id
                        or UUID("00000000-0000-0000-0000-000000000000"),
                        entity_data=entity_data,
                    )

                    # Send as sync response with single change (for immediate application)
                    response = WebSocketSyncResponseSchema(
                        day_context=None,
                        changes=[entity_change],
                        last_audit_log_timestamp=audit_log_entity.occurred_at.isoformat(),
                    )

                    await send_ws_message(websocket, response.model_dump(mode="json"))
                    logger.debug(
                        f"Sent real-time entity change for {audit_log_entity.entity_type} {audit_log_entity.entity_id}"
                    )
                except Exception as deserialize_error:
                    logger.error(
                        f"Failed to deserialize audit log message: {deserialize_error}"
                    )
                    # Continue loop to avoid breaking the connection on bad messages

        except Exception as e:
            logger.error(f"Error in real-time events handler: {e}")
            break
