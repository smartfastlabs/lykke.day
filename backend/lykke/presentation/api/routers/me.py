"""Endpoints for retrieving the current authenticated user."""

from datetime import datetime as dt_datetime, time as dt_time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

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
    AddReminderToDayCommand,
    AddReminderToDayHandler,
    AddRoutineDefinitionToDayCommand,
    AddRoutineDefinitionToDayHandler,
    RemoveAlarmFromDayCommand,
    RemoveAlarmFromDayHandler,
    RemoveReminderCommand,
    RemoveReminderHandler,
    RescheduleDayCommand,
    RescheduleDayHandler,
    ScheduleDayCommand,
    ScheduleDayHandler,
    UpdateAlarmStatusCommand,
    UpdateAlarmStatusHandler,
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)
from lykke.application.commands.user import UpdateUserCommand, UpdateUserHandler
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
    ReminderSchema,
    RoutineSchema,
    TaskSchema,
    UserSchema,
    UserUpdateSchema,
)
from lykke.presentation.api.schemas.mappers import (
    map_alarm_to_schema,
    map_brain_dump_to_schema,
    map_calendar_entry_to_schema,
    map_day_context_to_schema,
    map_day_to_schema,
    map_reminder_to_schema,
    map_routine_to_schema,
    map_task_to_schema,
    map_user_to_schema,
)
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user

router = APIRouter()


@router.get("", response_model=UserSchema)
async def get_current_user_profile(
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UserSchema:
    """Return the currently authenticated user."""
    return map_user_to_schema(user)


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
    return map_day_to_schema(context.day, brain_dump_items=context.brain_dump_items)


@router.put("/tomorrow/reschedule", response_model=DaySchema)
async def reschedule_tomorrow(
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DaySchema:
    """Reschedule tomorrow by cleaning up and recreating all non-adhoc tasks."""
    tomorrow = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(RescheduleDayHandler)
    context = await handler.handle(RescheduleDayCommand(date=tomorrow))
    return map_day_to_schema(context.day, brain_dump_items=context.brain_dump_items)


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
    return map_day_to_schema(context.day, brain_dump_items=context.brain_dump_items)


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
# Today's Reminders
# ============================================================================


@router.post("/today/reminders", response_model=ReminderSchema)
async def add_reminder_to_today(
    name: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Add a reminder to today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(AddReminderToDayHandler)
    reminder = await handler.handle(AddReminderToDayCommand(date=date, reminder=name))
    return map_reminder_to_schema(reminder)


# ============================================================================
# Tomorrow's Reminders
# ============================================================================


@router.post("/tomorrow/reminders", response_model=ReminderSchema)
async def add_reminder_to_tomorrow(
    name: str,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Add a reminder to tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(AddReminderToDayHandler)
    reminder = await handler.handle(AddReminderToDayCommand(date=date, reminder=name))
    return map_reminder_to_schema(reminder)


@router.patch("/tomorrow/reminders/{reminder_id}", response_model=ReminderSchema)
async def update_tomorrow_reminder_status(
    reminder_id: UUID,
    status: value_objects.ReminderStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Update a reminder's status for tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(UpdateReminderStatusHandler)
    reminder = await handler.handle(
        UpdateReminderStatusCommand(date=date, reminder_id=reminder_id, status=status)
    )
    return map_reminder_to_schema(reminder)


@router.delete("/tomorrow/reminders/{reminder_id}", response_model=ReminderSchema)
async def remove_reminder_from_tomorrow(
    reminder_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Remove a reminder from tomorrow."""
    date = get_tomorrows_date(user.settings.timezone)
    handler = command_factory.create(RemoveReminderHandler)
    reminder = await handler.handle(
        RemoveReminderCommand(date=date, reminder_id=reminder_id)
    )
    return map_reminder_to_schema(reminder)


@router.patch("/today/reminders/{reminder_id}", response_model=ReminderSchema)
async def update_today_reminder_status(
    reminder_id: UUID,
    status: value_objects.ReminderStatus,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Update a reminder's status for today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(UpdateReminderStatusHandler)
    reminder = await handler.handle(
        UpdateReminderStatusCommand(date=date, reminder_id=reminder_id, status=status)
    )
    return map_reminder_to_schema(reminder)


@router.delete("/today/reminders/{reminder_id}", response_model=ReminderSchema)
async def remove_reminder_from_today(
    reminder_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ReminderSchema:
    """Remove a reminder from today."""
    date = get_current_date(user.settings.timezone)
    handler = command_factory.create(RemoveReminderHandler)
    reminder = await handler.handle(
        RemoveReminderCommand(date=date, reminder_id=reminder_id)
    )
    return map_reminder_to_schema(reminder)


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
