"""Endpoints for retrieving the current authenticated user."""

from datetime import UTC, datetime as dt_datetime, time as dt_time
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from lykke.application.commands.brain_dump import (
    CreateBrainDumpCommand,
    CreateBrainDumpHandler,
    DeleteBrainDumpCommand,
    DeleteBrainDumpHandler,
    UpdateBrainDumpStatusCommand,
    UpdateBrainDumpStatusHandler,
)
from lykke.application.commands.day import (
    AddAlarmToDayCommand,
    AddAlarmToDayHandler,
    AddRoutineDefinitionToDayCommand,
    AddRoutineDefinitionToDayHandler,
    RemoveAlarmFromDayCommand,
    RemoveAlarmFromDayHandler,
    RescheduleDayCommand,
    RescheduleDayHandler,
    ScheduleDayCommand,
    ScheduleDayHandler,
    UpdateAlarmStatusCommand,
    UpdateAlarmStatusHandler,
)
from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import GetDayContextHandler, GetDayContextQuery
from lykke.application.queries.list_base_personalities import (
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import (
    get_current_date,
    get_current_datetime_in_timezone,
    get_tomorrows_date,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserUpdateObject
from lykke.presentation.api.schemas import (
    AlarmSchema,
    BasePersonalitySchema,
    BrainDumpSchema,
    CalendarEntrySchema,
    DayContextSchema,
    DaySchema,
    RoutineSchema,
    TaskSchema,
    UserSchema,
    UserUpdateSchema,
)
from lykke.presentation.api.schemas.admin import DomainEventSchema
from lykke.presentation.api.schemas.mappers import (
    map_alarm_to_schema,
    map_brain_dump_to_schema,
    map_calendar_entry_to_schema,
    map_day_context_to_schema,
    map_day_to_schema,
    map_routine_to_schema,
    map_task_to_schema,
    map_user_to_schema,
)
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.services import get_pubsub_gateway
from .dependencies.user import get_current_user, get_current_user_from_token

router = APIRouter()


def _build_domain_event_payload(message: dict[str, Any]) -> DomainEventSchema | None:
    event_type = message.get("event_type")
    event_data = message.get("event_data")
    if not isinstance(event_type, str) or not isinstance(event_data, dict):
        return None

    stored_at = message.get("stored_at")
    if isinstance(stored_at, str):
        try:
            stored_at = dt_datetime.fromisoformat(stored_at)
        except ValueError:
            stored_at = None
    if not isinstance(stored_at, dt_datetime):
        stored_at = dt_datetime.now(UTC)

    event_id = message.get("id")
    if not isinstance(event_id, str):
        event_id = str(uuid4())

    return DomainEventSchema(
        id=event_id,
        event_type=event_type,
        event_data=event_data,
        stored_at=stored_at,
    )


@router.get("", response_model=UserSchema)
async def get_current_user_profile(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserSchema:
    """Return the currently authenticated user."""
    return map_user_to_schema(user)


@router.websocket("/admin/domain-events")
async def domain_events_stream(
    websocket: WebSocket,
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
) -> None:
    """WebSocket endpoint for real-time domain events for the current user."""
    await websocket.accept()
    try:
        async with pubsub_gateway.subscribe_to_user_channel(
            user_id=user.id, channel_type="domain-events"
        ) as subscription:
            while True:
                payload = await subscription.get_message(timeout=1.0)
                if payload:
                    event_payload = _build_domain_event_payload(payload)
                    if event_payload is None:
                        continue
                    await websocket.send_json(
                        {
                            "type": "domain_event",
                            "data": event_payload.model_dump(mode="json"),
                        }
                    )
    except WebSocketDisconnect:
        logger.info(f"Domain events WebSocket disconnected for user {user.id}")
    except Exception as exc:
        logger.error(f"Domain events WebSocket error: {exc}")
        try:
            await websocket.send_json(
                {"type": "error", "message": "An unexpected error occurred"}
            )
            await websocket.close()
        except Exception:
            pass


@router.put("", response_model=UserSchema)
async def update_current_user_profile(
    update_data: UserUpdateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> UserSchema:
    """Update the current authenticated user."""
    update_user_handler = command_factory.create(UpdateUserHandler)
    settings_update = None
    if update_data.settings is not None:
        provided_settings = update_data.settings.model_dump(exclude_unset=True)
        settings_update = value_objects.UserSettingUpdate.from_dict(provided_settings)

    update_object = UserUpdateObject(
        phone_number=update_data.phone_number,
        status=update_data.status,
        is_active=update_data.is_active,
        is_superuser=update_data.is_superuser,
        is_verified=update_data.is_verified,
        settings_update=settings_update,
    )
    updated_user = await update_user_handler.handle(
        UpdateUserCommand(update_data=update_object)
    )
    return map_user_to_schema(updated_user)


@router.get("/base-personalities", response_model=list[BasePersonalitySchema])
async def list_base_personalities(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> list[BasePersonalitySchema]:
    """List available base personalities."""
    handler = query_factory.create(ListBasePersonalitiesHandler)
    personalities = await handler.handle(ListBasePersonalitiesQuery())
    return [
        BasePersonalitySchema.model_validate(personality)
        for personality in personalities
    ]


# ============================================================================
# Tomorrow Context (Non-streaming)
# ============================================================================


async def _get_or_schedule_tomorrow_context(
    *,
    query_factory: QueryHandlerFactory,
    command_factory: CommandHandlerFactory,
    user_timezone: str | None,
) -> value_objects.DayContext:
    tomorrow = get_tomorrows_date(user_timezone)
    get_context_handler = query_factory.create(GetDayContextHandler)
    try:
        return await get_context_handler.handle(GetDayContextQuery(date=tomorrow))
    except NotFoundError:
        schedule_handler = command_factory.create(ScheduleDayHandler)
        return await schedule_handler.handle(ScheduleDayCommand(date=tomorrow))


async def _get_tomorrow_context(
    *,
    query_factory: QueryHandlerFactory,
    user_timezone: str | None,
) -> value_objects.DayContext:
    """Get tomorrow's context, requiring it to already exist."""
    tomorrow = get_tomorrows_date(user_timezone)
    handler = query_factory.create(GetDayContextHandler)
    return await handler.handle(GetDayContextQuery(date=tomorrow))


@router.post("/tomorrow/ensure-scheduled", response_model=DaySchema)
async def ensure_tomorrow_scheduled(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DaySchema:
    """Ensure tomorrow exists and is scheduled. Returns the Day."""
    context = await _get_or_schedule_tomorrow_context(
        query_factory=query_factory,
        command_factory=command_factory,
        user_timezone=user.settings.timezone,
    )
    return map_day_to_schema(context.day, brain_dumps=context.brain_dumps)


@router.put("/tomorrow/reschedule", response_model=DaySchema)
async def reschedule_tomorrow(
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DaySchema:
    """Reschedule tomorrow by cleaning up and recreating all non-adhoc tasks."""
    tomorrow = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(RescheduleDayHandler)
    context = await handler.handle(RescheduleDayCommand(date=tomorrow))
    return map_day_to_schema(context.day, brain_dumps=context.brain_dumps)


@router.get("/tomorrow/day", response_model=DaySchema)
async def get_tomorrow_day(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DaySchema:
    """Get tomorrow's Day (requires it to be scheduled)."""
    context = await _get_tomorrow_context(
        query_factory=query_factory,
        user_timezone=user.settings.timezone,
    )
    return map_day_to_schema(context.day, brain_dumps=context.brain_dumps)


@router.get("/tomorrow/calendar-entries", response_model=list[CalendarEntrySchema])
async def get_tomorrow_calendar_entries(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[CalendarEntrySchema]:
    """Get tomorrow's calendar entries (requires it to be scheduled)."""
    context = await _get_tomorrow_context(
        query_factory=query_factory,
        user_timezone=user.settings.timezone,
    )
    return [
        map_calendar_entry_to_schema(entry, user_timezone=user.settings.timezone)
        for entry in context.calendar_entries
    ]


@router.get("/tomorrow/tasks", response_model=list[TaskSchema])
async def get_tomorrow_tasks(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Get tomorrow's tasks (requires it to be scheduled)."""
    context = await _get_tomorrow_context(
        query_factory=query_factory,
        user_timezone=user.settings.timezone,
    )
    current_time = get_current_datetime_in_timezone(user.settings.timezone)
    return [
        map_task_to_schema(
            task, current_time=current_time, user_timezone=user.settings.timezone
        )
        for task in context.tasks
    ]


@router.get("/tomorrow/routines", response_model=list[RoutineSchema])
async def get_tomorrow_routines(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[RoutineSchema]:
    """Get tomorrow's routines (requires it to be scheduled)."""
    context = await _get_tomorrow_context(
        query_factory=query_factory,
        user_timezone=user.settings.timezone,
    )
    current_time = get_current_datetime_in_timezone(user.settings.timezone)
    return [
        map_routine_to_schema(
            routine,
            tasks=context.tasks,
            current_time=current_time,
            user_timezone=user.settings.timezone,
        )
        for routine in context.routines
    ]


@router.get("/tomorrow/context", response_model=DayContextSchema)
async def get_tomorrow_context(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DayContextSchema:
    """Get tomorrow's full DayContext snapshot (requires it to be scheduled)."""
    context = await _get_tomorrow_context(
        query_factory=query_factory, user_timezone=user.settings.timezone
    )
    return map_day_context_to_schema(context, user_timezone=user.settings.timezone)


# ============================================================================
# Today's Alarms
# ============================================================================


@router.post("/today/alarms", response_model=AlarmSchema)
async def add_alarm_to_today(
    time: dt_time,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    name: str | None = None,
    alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL,
    url: str = "",
) -> AlarmSchema:
    """Add an alarm to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(AddAlarmToDayHandler)
    alarm = await handler.handle(
        AddAlarmToDayCommand(
            date=date,
            name=name,
            time=time,
            alarm_type=alarm_type,
            url=url,
        )
    )
    return map_alarm_to_schema(alarm)


# ============================================================================
# Tomorrow's Alarms
# ============================================================================


@router.post("/tomorrow/alarms", response_model=AlarmSchema)
async def add_alarm_to_tomorrow(
    time: dt_time,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    name: str | None = None,
    alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL,
    url: str = "",
) -> AlarmSchema:
    """Add an alarm to tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(AddAlarmToDayHandler)
    alarm = await handler.handle(
        AddAlarmToDayCommand(
            date=date,
            name=name,
            time=time,
            alarm_type=alarm_type,
            url=url,
        )
    )
    return map_alarm_to_schema(alarm)


@router.delete("/tomorrow/alarms", response_model=AlarmSchema)
async def remove_alarm_from_tomorrow(
    name: str,
    time: dt_time,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    alarm_type: value_objects.AlarmType | None = None,
    url: str | None = None,
) -> AlarmSchema:
    """Remove an alarm from tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(RemoveAlarmFromDayHandler)
    alarm = await handler.handle(
        RemoveAlarmFromDayCommand(
            date=date,
            name=name,
            time=time,
            alarm_type=alarm_type,
            url=url,
        )
    )
    return map_alarm_to_schema(alarm)


@router.patch("/tomorrow/alarms/{alarm_id}", response_model=AlarmSchema)
async def update_alarm_status_for_tomorrow(
    alarm_id: UUID,
    status: value_objects.AlarmStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    snoozed_until: dt_datetime | None = None,
) -> AlarmSchema:
    """Update an alarm's status for tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(UpdateAlarmStatusHandler)
    alarm = await handler.handle(
        UpdateAlarmStatusCommand(
            date=date,
            alarm_id=alarm_id,
            status=status,
            snoozed_until=snoozed_until,
        )
    )
    return map_alarm_to_schema(alarm)


@router.delete("/today/alarms", response_model=AlarmSchema)
async def remove_alarm_from_today(
    name: str,
    time: dt_time,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    alarm_type: value_objects.AlarmType | None = None,
    url: str | None = None,
) -> AlarmSchema:
    """Remove an alarm from today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(RemoveAlarmFromDayHandler)
    alarm = await handler.handle(
        RemoveAlarmFromDayCommand(
            date=date,
            name=name,
            time=time,
            alarm_type=alarm_type,
            url=url,
        )
    )
    return map_alarm_to_schema(alarm)


@router.patch("/today/alarms/{alarm_id}", response_model=AlarmSchema)
async def update_alarm_status_for_today(
    alarm_id: UUID,
    status: value_objects.AlarmStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
    snoozed_until: dt_datetime | None = None,
) -> AlarmSchema:
    """Update an alarm's status for today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(UpdateAlarmStatusHandler)
    alarm = await handler.handle(
        UpdateAlarmStatusCommand(
            date=date,
            alarm_id=alarm_id,
            status=status,
            snoozed_until=snoozed_until,
        )
    )
    return map_alarm_to_schema(alarm)


# ============================================================================
# Today's Brain Dump
# ============================================================================


@router.post("/today/brain-dump", response_model=BrainDumpSchema)
async def add_brain_dump_to_today(
    text: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpSchema:
    """Add a brain dump to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(CreateBrainDumpHandler)
    item = await handler.handle(CreateBrainDumpCommand(date=date, text=text))
    return map_brain_dump_to_schema(item)


@router.patch("/today/brain-dump/{item_id}", response_model=BrainDumpSchema)
async def update_brain_dump_status(
    item_id: UUID,
    status: value_objects.BrainDumpStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpSchema:
    """Update a brain dump's status for today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(UpdateBrainDumpStatusHandler)
    item = await handler.handle(
        UpdateBrainDumpStatusCommand(date=date, item_id=item_id, status=status)
    )
    return map_brain_dump_to_schema(item)


@router.delete("/today/brain-dump/{item_id}", response_model=BrainDumpSchema)
async def remove_brain_dump_from_today(
    item_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> BrainDumpSchema:
    """Remove a brain dump from today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(DeleteBrainDumpHandler)
    item = await handler.handle(DeleteBrainDumpCommand(date=date, item_id=item_id))
    return map_brain_dump_to_schema(item)


# ============================================================================
# Today's Routines
# ============================================================================


@router.post("/today/routines", response_model=list[TaskSchema])
async def add_routine_to_today(
    routine_definition_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Add a routine's tasks to today (creates today's routine if needed)."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(AddRoutineDefinitionToDayHandler)
    tasks = await handler.handle(
        AddRoutineDefinitionToDayCommand(
            date=date,
            routine_definition_id=routine_definition_id,
        )
    )
    return [map_task_to_schema(task) for task in tasks]


@router.post("/tomorrow/routines", response_model=list[TaskSchema])
async def add_routine_to_tomorrow(
    routine_definition_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Add a routine's tasks to tomorrow (creates tomorrow's routine if needed)."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(AddRoutineDefinitionToDayHandler)
    tasks = await handler.handle(
        AddRoutineDefinitionToDayCommand(
            date=date,
            routine_definition_id=routine_definition_id,
        )
    )
    return [map_task_to_schema(task) for task in tasks]
