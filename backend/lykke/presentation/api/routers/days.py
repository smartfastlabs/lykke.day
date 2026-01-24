"""Routes for day operations."""

import asyncio
import contextlib
import json
from datetime import UTC, date, datetime as dt_datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.commands import (
    RescheduleDayCommand,
    RescheduleDayHandler,
    ScheduleDayCommand,
    ScheduleDayHandler,
    UpdateDayCommand,
    UpdateDayHandler,
)
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import (
    GetDayContextHandler,
    GetDayContextQuery,
    GetIncrementalChangesHandler,
    GetIncrementalChangesQuery,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_date
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import DayUpdateObject
from lykke.presentation.api.schemas import DayContextSchema, DaySchema, DayUpdateSchema
from lykke.presentation.api.schemas.mappers import (
    map_day_context_to_schema,
    map_day_to_schema,
)
from lykke.presentation.api.schemas.websocket_message import (
    EntityChangeSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketSyncRequestSchema,
    WebSocketSyncResponseSchema,
)
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory
from .dependencies.services import (
    day_context_handler_websocket,
    get_pubsub_gateway,
    get_read_only_repository_factory,
    get_schedule_day_handler_websocket,
    incremental_changes_handler_websocket,
)
from .dependencies.user import get_current_user

router = APIRouter()


# ============================================================================
# Day Context Queries
# ============================================================================


@router.put("/today/reschedule", response_model=DayContextSchema)
async def reschedule_today(
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DayContextSchema:
    """Reschedule today by cleaning up and recreating all tasks."""
    today = get_current_date(user.settings.timezone)
    handler = command_factory.create(RescheduleDayHandler)
    context = await handler.handle(RescheduleDayCommand(date=today))
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


@router.patch("/{day_id}", response_model=DaySchema)
async def update_day(
    day_id: UUID,
    update_data: DayUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> DaySchema:
    """Update a day."""
    update_day_handler = command_factory.create(UpdateDayHandler)
    ro_repos = ro_repo_factory.create(user.id)
    day = await ro_repos.day_ro_repo.get(day_id)

    status = update_data.status
    if (
        status is None
        and update_data.high_level_plan is not None
        and day.status == value_objects.DayStatus.SCHEDULED
    ):
        status = value_objects.DayStatus.STARTED

    update_object = DayUpdateObject(
        status=status,
        scheduled_at=update_data.scheduled_at,
        tags=update_data.tags,
        template_id=update_data.template_id,
        high_level_plan=(
            value_objects.HighLevelPlan(
                title=update_data.high_level_plan.title,
                text=update_data.high_level_plan.text,
                intentions=update_data.high_level_plan.intentions or [],
            )
            if update_data.high_level_plan
            else None
        ),
    )
    updated = await update_day_handler.handle(
        UpdateDayCommand(date=day.date, update_data=update_object)
    )
    return map_day_to_schema(updated)


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
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
    day_context_handler: Annotated[
        GetDayContextHandler, Depends(day_context_handler_websocket)
    ],
    incremental_changes_handler_ws: Annotated[
        GetIncrementalChangesHandler,
        Depends(incremental_changes_handler_websocket),
    ],
    schedule_day_handler: Annotated[
        ScheduleDayHandler, Depends(get_schedule_day_handler_websocket)
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

        # Get today's date in the user's timezone
        user_timezone = None
        try:
            user = await day_context_handler.user_ro_repo.get(user_id)
            user_timezone = user.settings.timezone if user.settings else None
        except Exception:
            user_timezone = None
        today_date = get_current_date(user_timezone)

        # Subscribe to user's domain-events channel for real-time updates
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="domain-events"
        ) as domain_events_subscription:
            # Create tasks for handling messages and real-time events
            message_task = asyncio.create_task(
                _handle_client_messages(
                    websocket,
                    day_context_handler,
                    incremental_changes_handler_ws,
                    schedule_day_handler,
                    today_date,
                    user_timezone,
                )
            )
            events_task = asyncio.create_task(
                _handle_realtime_events(
                    websocket,
                    domain_events_subscription,
                    today_date,
                    incremental_changes_handler_ws,
                    user_timezone,
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
    schedule_day_handler: ScheduleDayHandler,
    today_date: date,
    user_timezone: str | None,
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
                    ) = await get_incremental_changes_handler.handle(
                        GetIncrementalChangesQuery(since=since_dt, date=today_date)
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
                    try:
                        context = await get_day_context_handler.handle(
                            GetDayContextQuery(date=today_date)
                        )
                    except NotFoundError:
                        # Day doesn't exist, auto-schedule it (WebSocket is THE place that creates Day if missing)
                        context = await schedule_day_handler.handle(
                            ScheduleDayCommand(date=today_date)
                        )

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

                    if last_audit_timestamp is None:
                        last_audit_timestamp = dt_datetime.now(UTC)

                    # Fetch all routines for the user
                    from lykke.presentation.api.schemas.mappers import (
                        map_routine_to_schema,
                    )

                    routines = await get_day_context_handler.routine_ro_repo.all()
                    routine_schemas = [
                        map_routine_to_schema(routine) for routine in routines
                    ]

                    response = WebSocketSyncResponseSchema(
                        day_context=map_day_context_to_schema(
                            context, user_timezone=user_timezone
                        ),
                        changes=None,
                        routines=routine_schemas,
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
    domain_events_subscription: Any,
    today_date: date,
    incremental_changes_handler: GetIncrementalChangesHandler,
    user_timezone: str | None,
) -> None:
    """Handle real-time domain events from pubsub and convert to entity changes.

    Filters to only AuditableDomainEvents and converts them to entity change
    notifications for today's entities.

    Args:
        websocket: WebSocket connection
        domain_events_subscription: PubSub subscription for domain events
        today_date: Today's date for filtering
        incremental_changes_handler: Handler to access repositories and load entity data
    """

    from lykke.core.utils.domain_event_serialization import deserialize_domain_event

    while True:
        try:
            # Wait for domain events from Redis with timeout
            domain_event_message = await domain_events_subscription.get_message(
                timeout=1.0
            )

            if domain_event_message:
                logger.debug("Received message from Redis subscription")
                try:
                    # Deserialize domain event
                    logger.debug("Received domain event message from Redis")
                    domain_event = deserialize_domain_event(domain_event_message)
                    logger.debug(
                        f"Deserialized domain event: {domain_event.__class__.__name__}"
                    )

                    # Only process events that identify an entity
                    if not domain_event.entity_id or not domain_event.entity_type:
                        logger.warning(
                            f"Domain event {domain_event.__class__.__name__} missing entity_id or entity_type"
                        )
                        continue

                    logger.debug(
                        f"Processing {domain_event.__class__.__name__} for {domain_event.entity_type} {domain_event.entity_id} on date {domain_event.entity_date}"
                    )

                    # Filter to today's entities using entity_date
                    entity_date = domain_event.entity_date
                    if isinstance(entity_date, dt_datetime):
                        entity_date = entity_date.date()

                    if entity_date and entity_date != today_date:
                        logger.debug(
                            f"Filtered out {domain_event.__class__.__name__} for entity {domain_event.entity_id} (not for today)"
                        )
                        continue

                    # For entities without entity_date (like routines), always include them
                    # They're not date-specific

                    # Determine change type from activity_type
                    activity_type = domain_event.__class__.__name__
                    change_type: Literal["created", "updated", "deleted"] | None = None
                    if (
                        "Created" in activity_type
                        or activity_type == "EntityCreatedEvent"
                    ):
                        change_type = "created"
                    elif (
                        "Deleted" in activity_type
                        or activity_type == "EntityDeletedEvent"
                    ):
                        change_type = "deleted"
                    elif (
                        "Updated" in activity_type
                        or "Added" in activity_type
                        or "Removed" in activity_type
                        or "StatusChanged" in activity_type
                        or "Completed" in activity_type
                        or "Scheduled" in activity_type
                        or "Unscheduled" in activity_type
                        or "Punted" in activity_type
                        or activity_type == "EntityUpdatedEvent"
                        or activity_type == "TaskCompletedEvent"
                        or activity_type == "TaskPuntedEvent"
                        or activity_type == "BrainDumpItemAddedEvent"
                        or activity_type == "BrainDumpItemStatusChangedEvent"
                        or activity_type == "BrainDumpItemRemovedEvent"
                    ):
                        change_type = "updated"
                    else:
                        # Skip events we don't know how to handle
                        logger.warning(f"Unknown activity type: {activity_type}")
                        continue

                    # Load entity data for created/updated entities
                    entity_data: dict[str, Any] | None = None
                    if change_type in ("created", "updated"):
                        try:
                            entity_id = domain_event.entity_id
                            if entity_id is not None:
                                entity_data = (
                                    await incremental_changes_handler._load_entity_data(
                                        domain_event.entity_type,
                                        entity_id,
                                        user_timezone=user_timezone,
                                    )
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to load entity data for {domain_event.entity_type} {domain_event.entity_id}: {e}"
                            )
                            # Continue without entity data - client can refetch if needed

                    # Create EntityChangeSchema
                    change = EntityChangeSchema(
                        change_type=change_type,
                        entity_type=domain_event.entity_type,
                        entity_id=domain_event.entity_id,
                        entity_data=entity_data,
                    )

                    # Send to client via WebSocket
                    last_audit_log_timestamp = domain_event.occurred_at.isoformat()

                    response = WebSocketSyncResponseSchema(
                        changes=[change],
                        day_context=None,
                        last_audit_log_timestamp=last_audit_log_timestamp,
                    )
                    logger.info(
                        f"Sending real-time update for {activity_type} on {domain_event.entity_type} {domain_event.entity_id}"
                    )
                    await send_ws_message(websocket, response.model_dump(mode="json"))
                    logger.info(
                        f"Successfully sent real-time update for {activity_type} on {domain_event.entity_type} {domain_event.entity_id}"
                    )

                except Exception as deserialize_error:
                    logger.error(
                        f"Failed to process domain event message: {deserialize_error}"
                    )
                    # Continue loop to avoid breaking the connection on bad messages

        except Exception as e:
            logger.error(f"Error in real-time events handler: {e}")
            break
