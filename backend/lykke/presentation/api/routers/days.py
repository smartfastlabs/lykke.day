"""Routes for day operations."""

import asyncio
import contextlib
import hashlib
import json
from datetime import UTC, date, datetime as dt_datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
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
    GetDayBrainDumpsHandler,
    GetDayBrainDumpsQuery,
    GetDayCalendarEntriesHandler,
    GetDayCalendarEntriesQuery,
    GetDayContextHandler,
    GetDayEntityHandler,
    GetDayEntityQuery,
    GetDayMessagesHandler,
    GetDayMessagesQuery,
    GetDayPushNotificationsHandler,
    GetDayPushNotificationsQuery,
    GetDayRoutinesHandler,
    GetDayRoutinesQuery,
    GetDayTasksHandler,
    GetDayTasksQuery,
    GetIncrementalChangesHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.core.utils.domain_event_serialization import (
    deserialize_domain_event,
    serialize_domain_event,
)
from lykke.domain import value_objects
from lykke.domain.entities import (
    BrainDumpEntity,
    CalendarEntryEntity,
    DayEntity,
    MessageEntity,
    PushNotificationEntity,
    RoutineEntity,
    TaskEntity,
    UserEntity,
)
from lykke.domain.events.day_events import NewDayEvent
from lykke.domain.value_objects import DayUpdateObject
from lykke.presentation.api.schemas import DayContextSchema, DaySchema, DayUpdateSchema
from lykke.presentation.api.schemas.mappers import (
    map_brain_dump_to_schema,
    map_calendar_entry_to_schema,
    map_day_context_to_schema,
    map_day_to_schema,
    map_message_to_schema,
    map_push_notification_to_schema,
    map_routine_to_schema,
    map_task_to_schema,
)
from lykke.presentation.api.schemas.websocket_message import (
    DayContextPartialSchema,
    DayContextPartKey,
    EntityChangeSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketSubscriptionSchema,
    WebSocketSyncRequestSchema,
    WebSocketSyncResponseSchema,
    WebSocketTopicEventSchema,
)
from lykke.presentation.handler_factory import CommandHandlerFactory

from .dependencies.factories import command_handler_factory
from .dependencies.services import (
    DayContextPartHandlers,
    day_context_handler_websocket,
    day_context_part_handlers_websocket,
    get_pubsub_gateway,
    get_pubsub_gateway_for_request,
    get_read_only_repository_factory,
    get_schedule_day_handler_websocket,
    incremental_changes_handler_websocket,
)
from .dependencies.user import get_current_user

router = APIRouter()

DAY_CONTEXT_PART_ORDER: tuple[DayContextPartKey, ...] = (
    "day",
    "tasks",
    "calendar_entries",
    "routines",
    "brain_dumps",
    "push_notifications",
    "messages",
)


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
    ro_repos = ro_repo_factory.create(user)
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
    brain_dumps = await ro_repos.brain_dump_ro_repo.search(
        value_objects.BrainDumpQuery(date=day.date)
    )
    return map_day_to_schema(updated, brain_dumps=brain_dumps)


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


async def _get_last_sync_state(
    *, pubsub_gateway: PubSubGatewayProtocol, user_id: UUID
) -> tuple[str | None, str | None]:
    last_change_stream_id: str | None = None
    last_audit_timestamp: str | None = None
    latest_entry = await pubsub_gateway.get_latest_user_stream_entry(
        user_id=user_id, stream_type="entity-changes"
    )
    if latest_entry:
        last_change_stream_id, latest_payload = latest_entry
        if isinstance(latest_payload, dict):
            last_audit_timestamp = latest_payload.get(
                "occurred_at"
            ) or latest_payload.get("stored_at")
    if last_audit_timestamp is None:
        last_audit_timestamp = dt_datetime.now(UTC).isoformat()
    return last_change_stream_id, last_audit_timestamp


def _build_partial_context(
    *,
    part_key: DayContextPartKey,
    day: DayEntity | None = None,
    tasks: list[TaskEntity] | None = None,
    calendar_entries: list[CalendarEntryEntity] | None = None,
    routines: list[RoutineEntity] | None = None,
    brain_dumps: list[BrainDumpEntity] | None = None,
    push_notifications: list[PushNotificationEntity] | None = None,
    messages: list[MessageEntity] | None = None,
    user_timezone: str | None,
) -> DayContextPartialSchema:
    current_time = get_current_datetime_in_timezone(user_timezone)

    if part_key == "day":
        if day is None:
            raise ValueError("Day is required for day context part.")
        return DayContextPartialSchema(
            day=map_day_to_schema(day, brain_dumps=brain_dumps or []),
        )
    if part_key == "tasks":
        return DayContextPartialSchema(
            tasks=[
                map_task_to_schema(
                    task, current_time=current_time, user_timezone=user_timezone
                )
                for task in (tasks or [])
            ],
        )
    if part_key == "calendar_entries":
        return DayContextPartialSchema(
            calendar_entries=[
                map_calendar_entry_to_schema(entry, user_timezone=user_timezone)
                for entry in (calendar_entries or [])
            ],
        )
    if part_key == "routines":
        return DayContextPartialSchema(
            routines=[
                map_routine_to_schema(
                    routine,
                    tasks=list(tasks) if tasks is not None else None,
                    current_time=current_time,
                    user_timezone=user_timezone,
                )
                for routine in (routines or [])
            ],
        )
    if part_key == "brain_dumps":
        return DayContextPartialSchema(
            brain_dumps=[
                map_brain_dump_to_schema(item) for item in (brain_dumps or [])
            ],
        )
    if part_key == "push_notifications":
        return DayContextPartialSchema(
            push_notifications=[
                map_push_notification_to_schema(notification)
                for notification in (push_notifications or [])
            ],
        )
    if part_key == "messages":
        return DayContextPartialSchema(
            messages=[map_message_to_schema(message) for message in (messages or [])],
        )

    raise ValueError(f"Unsupported day context part key: {part_key}")


async def _ensure_day_context(
    *,
    date_value: date,
    part_handlers: DayContextPartHandlers,
    schedule_day_handler: ScheduleDayHandler,
) -> tuple[value_objects.DayContext | None, DayEntity]:
    try:
        day = await part_handlers.day.handle(GetDayEntityQuery(date=date_value))
        return None, day
    except NotFoundError:
        context = await schedule_day_handler.handle(ScheduleDayCommand(date=date_value))
        return context, context.day


async def _load_day_context_part(
    *,
    part_key: DayContextPartKey,
    date_value: date,
    user_timezone: str | None,
    part_handlers: DayContextPartHandlers,
    context_cache: value_objects.DayContext | None,
    day_entity: DayEntity,
    tasks_cache: list[TaskEntity] | None,
) -> tuple[DayContextPartialSchema, list[TaskEntity] | None]:
    if context_cache:
        if part_key == "day":
            return (
                _build_partial_context(
                    part_key=part_key,
                    day=context_cache.day,
                    brain_dumps=context_cache.brain_dumps,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "tasks":
            tasks_cache = list(context_cache.tasks)
            return (
                _build_partial_context(
                    part_key=part_key,
                    tasks=tasks_cache,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "calendar_entries":
            return (
                _build_partial_context(
                    part_key=part_key,
                    calendar_entries=context_cache.calendar_entries,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "routines":
            return (
                _build_partial_context(
                    part_key=part_key,
                    routines=context_cache.routines,
                    tasks=tasks_cache or list(context_cache.tasks),
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "brain_dumps":
            return (
                _build_partial_context(
                    part_key=part_key,
                    brain_dumps=context_cache.brain_dumps,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "push_notifications":
            return (
                _build_partial_context(
                    part_key=part_key,
                    push_notifications=context_cache.push_notifications,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )
        if part_key == "messages":
            return (
                _build_partial_context(
                    part_key=part_key,
                    messages=context_cache.messages,
                    user_timezone=user_timezone,
                ),
                tasks_cache,
            )

    if part_key == "day":
        return (
            _build_partial_context(
                part_key=part_key,
                day=day_entity,
                brain_dumps=[],
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "tasks":
        tasks_cache = await part_handlers.tasks.handle(
            GetDayTasksQuery(date=date_value)
        )
        return (
            _build_partial_context(
                part_key=part_key,
                tasks=tasks_cache,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "calendar_entries":
        calendar_entries = await part_handlers.calendar_entries.handle(
            GetDayCalendarEntriesQuery(date=date_value)
        )
        return (
            _build_partial_context(
                part_key=part_key,
                calendar_entries=calendar_entries,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "routines":
        if tasks_cache is None:
            tasks_cache = await part_handlers.tasks.handle(
                GetDayTasksQuery(date=date_value)
            )
        routines = await part_handlers.routines.get_routines(
            date_value, tasks=tasks_cache
        )
        return (
            _build_partial_context(
                part_key=part_key,
                routines=routines,
                tasks=tasks_cache,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "brain_dumps":
        brain_dumps = await part_handlers.brain_dumps.handle(
            GetDayBrainDumpsQuery(date=date_value)
        )
        return (
            _build_partial_context(
                part_key=part_key,
                brain_dumps=brain_dumps,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "push_notifications":
        push_notifications = await part_handlers.push_notifications.handle(
            GetDayPushNotificationsQuery(date=date_value)
        )
        return (
            _build_partial_context(
                part_key=part_key,
                push_notifications=push_notifications,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )
    if part_key == "messages":
        messages = await part_handlers.messages.handle(
            GetDayMessagesQuery(date=date_value)
        )
        return (
            _build_partial_context(
                part_key=part_key,
                messages=messages,
                user_timezone=user_timezone,
            ),
            tasks_cache,
        )

    raise ValueError(f"Unsupported day context part key: {part_key}")


async def _send_day_context_parts(
    *,
    websocket: WebSocket,
    part_handlers: DayContextPartHandlers,
    schedule_day_handler: ScheduleDayHandler,
    pubsub_gateway: PubSubGatewayProtocol,
    user_id: UUID,
    date_value: date,
    user_timezone: str | None,
    parts: list[DayContextPartKey],
) -> str | None:
    if not parts:
        parts = list(DAY_CONTEXT_PART_ORDER)

    context_cache, day_entity = await _ensure_day_context(
        date_value=date_value,
        part_handlers=part_handlers,
        schedule_day_handler=schedule_day_handler,
    )
    tasks_cache: list[TaskEntity] | None = (
        list(context_cache.tasks) if context_cache else None
    )

    last_change_stream_id, last_audit_timestamp = await _get_last_sync_state(
        pubsub_gateway=pubsub_gateway,
        user_id=user_id,
    )

    for index, part_key in enumerate(parts):
        partial_context, tasks_cache = await _load_day_context_part(
            part_key=part_key,
            date_value=date_value,
            user_timezone=user_timezone,
            part_handlers=part_handlers,
            context_cache=context_cache,
            day_entity=day_entity,
            tasks_cache=tasks_cache,
        )
        response = WebSocketSyncResponseSchema(
            day_context=None,
            changes=None,
            routines=None,
            partial_context=partial_context,
            partial_key=part_key,
            sync_complete=index == len(parts) - 1,
            last_audit_log_timestamp=last_audit_timestamp,
            last_change_stream_id=last_change_stream_id,
        )
        await send_ws_message(websocket, response.model_dump(mode="json"))

    return last_change_stream_id


@router.websocket("/today/context")
async def days_context_websocket(
    websocket: WebSocket,
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
    day_context_handler: Annotated[
        GetDayContextHandler, Depends(day_context_handler_websocket)
    ],
    day_context_part_handlers: Annotated[
        DayContextPartHandlers, Depends(day_context_part_handlers_websocket)
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
        user_id = day_context_handler.user.id
        logger.info(f"Days context WebSocket connection established for user {user_id}")

        ack = WebSocketConnectionAckSchema(user_id=user_id)
        await send_ws_message(websocket, ack.model_dump(mode="json"))

        user_timezone = None
        user_timezone = (
            day_context_handler.user.settings.timezone
            if day_context_handler.user.settings
            else None
        )
        today_date = get_current_date(user_timezone)
        date_state = {"value": today_date}
        subscription_state: dict[str, set[str]] = {"topics": set()}
        stream_state: dict[str, str] = {"last_id": "0-0"}
        latest_entry = await pubsub_gateway.get_latest_user_stream_entry(
            user_id=user_id, stream_type="entity-changes"
        )
        if latest_entry:
            stream_state["last_id"] = latest_entry[0]

        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user_id, channel_type="domain-events"
        ) as domain_events_subscription:
            message_task = asyncio.create_task(
                _handle_client_messages(
                    websocket,
                    day_context_handler,
                    day_context_part_handlers,
                    incremental_changes_handler_ws,
                    schedule_day_handler,
                    pubsub_gateway,
                    date_state,
                    user_timezone,
                    subscription_state,
                    stream_state,
                )
            )
            domain_events_task = asyncio.create_task(
                _handle_realtime_domain_events(
                    websocket,
                    domain_events_subscription,
                    day_context_handler,
                    day_context_part_handlers,
                    schedule_day_handler,
                    pubsub_gateway,
                    date_state,
                    user_timezone,
                    subscription_state,
                    stream_state,
                )
            )
            change_stream_task = asyncio.create_task(
                _handle_change_stream_events(
                    websocket,
                    pubsub_gateway,
                    incremental_changes_handler_ws,
                    date_state,
                    user_timezone,
                    stream_state,
                )
            )

            done, pending = await asyncio.wait(
                [message_task, domain_events_task, change_stream_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

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
            pass


async def _handle_client_messages(
    websocket: WebSocket,
    get_day_context_handler: GetDayContextHandler,
    day_context_part_handlers: DayContextPartHandlers,
    get_incremental_changes_handler: GetIncrementalChangesHandler,
    schedule_day_handler: ScheduleDayHandler,
    pubsub_gateway: PubSubGatewayProtocol,
    date_state: dict[str, date],
    user_timezone: str | None,
    subscription_state: dict[str, set[str]],
    stream_state: dict[str, str],
) -> None:
    """Handle messages from the client (sync requests).

    Args:
        websocket: WebSocket connection
        get_day_context_handler: Handler for getting full day context
        get_incremental_changes_handler: Handler for getting incremental changes
        date_state: Mutable container holding the current date
    """
    while True:
        try:
            message_text = await websocket.receive_text()
            message_data = json.loads(message_text)

            message_type = message_data.get("type")
            if message_type in ("subscribe", "unsubscribe"):
                try:
                    subscription_request = WebSocketSubscriptionSchema(**message_data)
                except Exception as e:
                    logger.warning(f"Invalid subscription request: {e}")
                    await send_error(
                        websocket, "INVALID_REQUEST", f"Invalid request: {e}"
                    )
                    continue

                topics = {topic for topic in subscription_request.topics if topic}
                if subscription_request.type == "subscribe":
                    subscription_state["topics"].update(topics)
                else:
                    subscription_state["topics"].difference_update(topics)
                continue

            try:
                sync_request = WebSocketSyncRequestSchema(**message_data)
            except Exception as e:
                logger.warning(f"Invalid sync request: {e}")
                await send_error(websocket, "INVALID_REQUEST", f"Invalid request: {e}")
                continue

            if sync_request.since_change_stream_id or sync_request.since_timestamp:
                try:
                    since_stream_id = sync_request.since_change_stream_id
                    if since_stream_id is None and sync_request.since_timestamp:
                        since_dt = dt_datetime.fromisoformat(
                            sync_request.since_timestamp.replace("Z", "+00:00")
                        )
                        if since_dt.tzinfo is None:
                            since_dt = since_dt.replace(tzinfo=UTC)
                        else:
                            since_dt = since_dt.astimezone(UTC)
                        since_stream_id = f"{int(since_dt.timestamp() * 1000)}-0"

                    (
                        changes,
                        last_stream_id,
                        last_timestamp,
                    ) = await _read_change_stream_since(
                        pubsub_gateway=pubsub_gateway,
                        get_incremental_changes_handler=get_incremental_changes_handler,
                        user_id=get_day_context_handler.user.id,
                        date_value=date_state["value"],
                        user_timezone=user_timezone,
                        since_stream_id=since_stream_id or "0-0",
                    )
                    if last_stream_id:
                        stream_state["last_id"] = last_stream_id

                    response = WebSocketSyncResponseSchema(
                        changes=changes,
                        day_context=None,
                        partial_context=None,
                        partial_key=None,
                        sync_complete=None,
                        last_audit_log_timestamp=last_timestamp,
                        last_change_stream_id=last_stream_id,
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
                parts = []
                if sync_request.partial_keys:
                    parts = list(sync_request.partial_keys)
                elif sync_request.partial_key:
                    parts = [sync_request.partial_key]
                else:
                    parts = list(DAY_CONTEXT_PART_ORDER)
                try:
                    last_stream_id = await _send_day_context_parts(
                        websocket=websocket,
                        part_handlers=day_context_part_handlers,
                        schedule_day_handler=schedule_day_handler,
                        pubsub_gateway=pubsub_gateway,
                        user_id=get_day_context_handler.user.id,
                        date_value=date_state["value"],
                        user_timezone=user_timezone,
                        parts=parts,
                    )
                    if last_stream_id:
                        stream_state["last_id"] = last_stream_id
                except Exception as e:
                    logger.error(f"Error getting day context parts: {e}")
                    await send_error(
                        websocket,
                        "INTERNAL_ERROR",
                        f"Failed to get day context parts: {e}",
                    )
                continue

            await send_ws_message(websocket, response.model_dump(mode="json"))

        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await send_error(
                websocket, "INTERNAL_ERROR", f"Error processing message: {e}"
            )


async def _handle_realtime_domain_events(
    websocket: WebSocket,
    domain_events_subscription: Any,
    day_context_handler: GetDayContextHandler,
    day_context_part_handlers: DayContextPartHandlers,
    schedule_day_handler: ScheduleDayHandler,
    pubsub_gateway: PubSubGatewayProtocol,
    date_state: dict[str, date],
    user_timezone: str | None,
    subscription_state: dict[str, set[str]],
    stream_state: dict[str, str],
) -> None:
    """Handle domain events for topic subscriptions and new day signals."""
    while True:
        try:
            domain_event_message = await domain_events_subscription.get_message(
                timeout=1.0
            )
            if not domain_event_message:
                continue
            try:
                domain_event = deserialize_domain_event(domain_event_message)
            except Exception as deserialize_error:
                logger.error(
                    f"Failed to process domain event message: {deserialize_error}"
                )
                continue

            if isinstance(domain_event, NewDayEvent):
                next_date = domain_event.date
                current_date = date_state["value"]
                if next_date != current_date:
                    logger.info(
                        f"New day detected ({current_date} -> {next_date}). Sending full sync.",
                    )
                    date_state["value"] = next_date
                    last_stream_id = await _send_day_context_parts(
                        websocket=websocket,
                        part_handlers=day_context_part_handlers,
                        schedule_day_handler=schedule_day_handler,
                        pubsub_gateway=pubsub_gateway,
                        user_id=day_context_handler.user.id,
                        date_value=next_date,
                        user_timezone=user_timezone,
                        parts=list(DAY_CONTEXT_PART_ORDER),
                    )
                    if last_stream_id:
                        stream_state["last_id"] = last_stream_id
                continue

            event_topic = domain_event.__class__.__name__
            if event_topic in subscription_state["topics"]:
                topic_event = WebSocketTopicEventSchema(
                    topic=event_topic,
                    event=serialize_domain_event(domain_event),
                )
                await send_ws_message(websocket, topic_event.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Error in domain event handler: {e}")
            break


async def _read_change_stream_since(
    *,
    pubsub_gateway: PubSubGatewayProtocol,
    get_incremental_changes_handler: GetIncrementalChangesHandler,
    user_id: UUID,
    date_value: date,
    user_timezone: str | None,
    since_stream_id: str,
) -> tuple[list[EntityChangeSchema], str | None, str | None]:
    """Read change stream entries since a stream id."""
    changes: list[EntityChangeSchema] = []
    last_stream_id: str | None = None
    last_timestamp: str | None = None
    current_id = since_stream_id

    while True:
        entries = await pubsub_gateway.read_user_stream(
            user_id=user_id,
            stream_type="entity-changes",
            last_id=current_id,
            count=200,
            block_ms=1,
        )
        if not entries:
            break

        for stream_id, payload in entries:
            current_id = stream_id
            last_stream_id = stream_id
            entity_date = payload.get("entity_date")
            if isinstance(entity_date, str):
                try:
                    parsed_date = date.fromisoformat(entity_date)
                except ValueError:
                    parsed_date = None
                if parsed_date is not None and parsed_date != date_value:
                    continue

            change = await _build_change_from_stream_payload(
                payload=payload,
                get_incremental_changes_handler=get_incremental_changes_handler,
                user_timezone=user_timezone,
            )
            if change is None:
                continue
            last_timestamp = payload.get("occurred_at") or payload.get("stored_at")
            changes.append(change)

    return changes, last_stream_id, last_timestamp


async def _build_change_from_stream_payload(
    *,
    payload: dict[str, Any],
    get_incremental_changes_handler: GetIncrementalChangesHandler,
    user_timezone: str | None,
) -> EntityChangeSchema | None:
    change_type = payload.get("change_type")
    entity_type = payload.get("entity_type")
    entity_id = payload.get("entity_id")
    if change_type not in ("created", "updated", "deleted"):
        return None
    if not isinstance(entity_type, str) or not isinstance(entity_id, str):
        return None
    try:
        entity_uuid = UUID(entity_id)
    except ValueError:
        return None

    entity_patch = payload.get("entity_patch")
    if not isinstance(entity_patch, list) or len(entity_patch) == 0:
        entity_patch = None

    entity_data: dict[str, Any] | None = None
    if change_type in ("created", "updated") and entity_patch is None:
        try:
            activity_type = (
                "EntityCreatedEvent"
                if change_type == "created"
                else "EntityUpdatedEvent"
            )
            entity_data = await get_incremental_changes_handler._load_entity_data(
                entity_type,
                entity_uuid,
                activity_type=activity_type,
                user_timezone=user_timezone,
            )
        except Exception as e:
            logger.error(
                f"Failed to load entity data for {entity_type} {entity_uuid}: {e}"
            )
            entity_data = None

    return EntityChangeSchema(
        change_type=change_type,
        entity_type=entity_type,
        entity_id=entity_uuid,
        entity_data=entity_data,
        entity_patch=entity_patch,
    )


async def _handle_change_stream_events(
    websocket: WebSocket,
    pubsub_gateway: PubSubGatewayProtocol,
    get_incremental_changes_handler: GetIncrementalChangesHandler,
    date_state: dict[str, date],
    user_timezone: str | None,
    stream_state: dict[str, str],
) -> None:
    """Handle real-time entity change stream events."""
    user_id = get_incremental_changes_handler.user.id
    while True:
        try:
            entries = await pubsub_gateway.read_user_stream(
                user_id=user_id,
                stream_type="entity-changes",
                last_id=stream_state["last_id"],
                count=100,
                block_ms=1000,
            )
            if not entries:
                continue

            for stream_id, payload in entries:
                stream_state["last_id"] = stream_id
                entity_date = payload.get("entity_date")
                if isinstance(entity_date, str):
                    try:
                        parsed_date = date.fromisoformat(entity_date)
                    except ValueError:
                        parsed_date = None
                    if parsed_date is not None and parsed_date != date_state["value"]:
                        continue

                change = await _build_change_from_stream_payload(
                    payload=payload,
                    get_incremental_changes_handler=get_incremental_changes_handler,
                    user_timezone=user_timezone,
                )
                if change is None:
                    continue

                last_timestamp = payload.get("occurred_at") or payload.get("stored_at")
                response = WebSocketSyncResponseSchema(
                    changes=[change],
                    day_context=None,
                    last_audit_log_timestamp=last_timestamp,
                    last_change_stream_id=stream_id,
                )
                await send_ws_message(websocket, response.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Error in change stream handler: {e}")
            break
