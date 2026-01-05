"""Mapper functions to convert domain entities to API schemas."""

from dataclasses import asdict

from planned.domain import value_objects
from planned.domain.entities import (
    CalendarEntity,
    CalendarEntryEntity,
    DayEntity,
    RoutineEntity,
    TaskEntity,
)
from planned.domain import data_objects
from planned.presentation.api.schemas import (
    ActionSchema,
    AlarmSchema,
    CalendarEntrySchema,
    CalendarSchema,
    DayContextSchema,
    DaySchema,
    DayTemplateSchema,
    PushSubscriptionSchema,
    RoutineSchema,
    TaskDefinitionSchema,
    TaskScheduleSchema,
    TaskSchema,
)


def map_action_to_schema(action: value_objects.Action) -> ActionSchema:
    """Convert Action entity to Action schema."""
    return ActionSchema(**asdict(action))


def map_alarm_to_schema(alarm: value_objects.Alarm) -> AlarmSchema:
    """Convert Alarm value object to Alarm schema."""
    return AlarmSchema(**asdict(alarm))


def map_task_definition_to_schema(
    task_definition: data_objects.TaskDefinition,
) -> TaskDefinitionSchema:
    """Convert TaskDefinition data object to TaskDefinition schema."""
    return TaskDefinitionSchema(**asdict(task_definition))


def map_task_schedule_to_schema(
    schedule: value_objects.TaskSchedule | None,
) -> TaskScheduleSchema | None:
    """Convert TaskSchedule value object to TaskSchedule schema."""
    if schedule is None:
        return None
    # TaskSchedule is already a Pydantic model, so we can validate it directly
    return TaskScheduleSchema.model_validate(schedule, from_attributes=True)


def map_task_to_schema(task: TaskEntity) -> TaskSchema:
    """Convert Task entity to Task schema."""
    # Convert nested entities
    task_definition_schema = map_task_definition_to_schema(task.task_definition)
    action_schemas = [map_action_to_schema(action) for action in task.actions]
    schedule_schema = map_task_schedule_to_schema(task.schedule)

    return TaskSchema(
        id=task.id,
        user_id=task.user_id,
        scheduled_date=task.scheduled_date,
        name=task.name,
        status=task.status,
        task_definition=task_definition_schema,
        category=task.category,
        frequency=task.frequency,
        completed_at=task.completed_at,
        schedule=schedule_schema,
        routine_id=task.routine_id,
        tags=task.tags,
        actions=action_schemas,
    )


def map_day_template_to_schema(
    template: data_objects.DayTemplate,
) -> DayTemplateSchema:
    """Convert DayTemplate data object to DayTemplate schema."""
    alarm_schema = map_alarm_to_schema(template.alarm) if template.alarm else None

    return DayTemplateSchema(
        id=template.id,
        user_id=template.user_id,
        slug=template.slug,
        alarm=alarm_schema,
        icon=template.icon,
        routine_ids=template.routine_ids,
    )


def map_day_to_schema(day: DayEntity) -> DaySchema:
    """Convert Day entity to Day schema."""
    alarm_schema = map_alarm_to_schema(day.alarm) if day.alarm else None
    template_schema = map_day_template_to_schema(day.template) if day.template else None

    return DaySchema(
        id=day.id,
        user_id=day.user_id,
        date=day.date,
        alarm=alarm_schema,
        status=day.status,
        scheduled_at=day.scheduled_at,
        tags=day.tags,
        template=template_schema,
    )


def map_calendar_entry_to_schema(
    entry: CalendarEntryEntity,
) -> CalendarEntrySchema:
    """Convert CalendarEntry entity to CalendarEntry schema."""
    action_schemas = [map_action_to_schema(action) for action in entry.actions]

    return CalendarEntrySchema(
        id=entry.id,
        user_id=entry.user_id,
        name=entry.name,
        calendar_id=entry.calendar_id,
        platform_id=entry.platform_id,
        platform=entry.platform,
        status=entry.status,
        starts_at=entry.starts_at,
        frequency=entry.frequency,
        ends_at=entry.ends_at,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        actions=action_schemas,
        date=entry.date,  # Computed field
    )


def map_day_context_to_schema(
    context: value_objects.DayContext,
) -> DayContextSchema:
    """Convert DayContext value object to DayContext schema."""
    day_schema = map_day_to_schema(context.day)
    calendar_entry_schemas = [
        map_calendar_entry_to_schema(entry) for entry in context.calendar_entries
    ]
    task_schemas = [map_task_to_schema(task) for task in context.tasks]

    return DayContextSchema(
        day=day_schema,
        calendar_entries=calendar_entry_schemas,
        tasks=task_schemas,
    )


def map_push_subscription_to_schema(
    subscription: data_objects.PushSubscription,
) -> PushSubscriptionSchema:
    """Convert PushSubscription entity to PushSubscription schema."""
    return PushSubscriptionSchema(**asdict(subscription))


def map_routine_to_schema(routine: RoutineEntity) -> RoutineSchema:
    """Convert Routine entity to Routine schema."""
    return RoutineSchema(**asdict(routine))


def map_calendar_to_schema(calendar: CalendarEntity) -> CalendarSchema:
    """Convert Calendar entity to Calendar schema."""
    return CalendarSchema(**asdict(calendar))
