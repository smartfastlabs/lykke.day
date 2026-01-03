"""Mapper functions to convert domain entities to API schemas."""

from dataclasses import asdict

from planned.domain import entities, value_objects
from planned.infrastructure import data_objects
from planned.presentation.api import schemas


def map_action_to_schema(action: entities.Action) -> schemas.Action:
    """Convert Action entity to Action schema."""
    return schemas.Action(**asdict(action))


def map_alarm_to_schema(alarm: value_objects.Alarm) -> schemas.Alarm:
    """Convert Alarm value object to Alarm schema."""
    return schemas.Alarm(**asdict(alarm))


def map_task_definition_to_schema(
    task_definition: entities.TaskDefinition,
) -> schemas.TaskDefinition:
    """Convert TaskDefinition entity to TaskDefinition schema."""
    return schemas.TaskDefinition(**asdict(task_definition))


def map_task_schedule_to_schema(
    schedule: value_objects.TaskSchedule | None,
) -> schemas.TaskSchedule | None:
    """Convert TaskSchedule value object to TaskSchedule schema."""
    if schedule is None:
        return None
    # TaskSchedule is already a Pydantic model, so we can validate it directly
    return schemas.TaskSchedule.model_validate(schedule, from_attributes=True)


def map_task_to_schema(task: entities.Task) -> schemas.Task:
    """Convert Task entity to Task schema."""
    # Convert nested entities
    task_definition_schema = map_task_definition_to_schema(task.task_definition)
    action_schemas = [map_action_to_schema(action) for action in task.actions]
    schedule_schema = map_task_schedule_to_schema(task.schedule)

    return schemas.Task(
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
    template: entities.DayTemplate,
) -> schemas.DayTemplate:
    """Convert DayTemplate entity to DayTemplate schema."""
    alarm_schema = map_alarm_to_schema(template.alarm) if template.alarm else None

    return schemas.DayTemplate(
        id=template.id,
        user_id=template.user_id,
        slug=template.slug,
        alarm=alarm_schema,
        icon=template.icon,
        routine_ids=template.routine_ids,
    )


def map_day_to_schema(day: entities.Day) -> schemas.Day:
    """Convert Day entity to Day schema."""
    alarm_schema = map_alarm_to_schema(day.alarm) if day.alarm else None
    template_schema = map_day_template_to_schema(day.template) if day.template else None

    return schemas.Day(
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
    entry: entities.CalendarEntry,
) -> schemas.CalendarEntry:
    """Convert CalendarEntry entity to CalendarEntry schema."""
    action_schemas = [map_action_to_schema(action) for action in entry.actions]

    return schemas.CalendarEntry(
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


def map_message_to_schema(message: entities.Message) -> schemas.Message:
    """Convert Message entity to Message schema."""
    return schemas.Message(
        id=message.id,
        user_id=message.user_id,
        author=message.author,
        sent_at=message.sent_at,
        content=message.content,
        read_at=message.read_at,
        date=message.date,  # Computed field
    )


def map_day_context_to_schema(
    context: value_objects.DayContext,
) -> schemas.DayContext:
    """Convert DayContext value object to DayContext schema."""
    day_schema = map_day_to_schema(context.day)
    calendar_entry_schemas = [
        map_calendar_entry_to_schema(entry) for entry in context.calendar_entries
    ]
    task_schemas = [map_task_to_schema(task) for task in context.tasks]
    message_schemas = [map_message_to_schema(message) for message in context.messages]

    return schemas.DayContext(
        day=day_schema,
        calendar_entries=calendar_entry_schemas,
        tasks=task_schemas,
        messages=message_schemas,
    )


def map_push_subscription_to_schema(
    subscription: data_objects.PushSubscription,
) -> schemas.PushSubscription:
    """Convert PushSubscription entity to PushSubscription schema."""
    return schemas.PushSubscription(**asdict(subscription))


def map_routine_to_schema(routine: entities.Routine) -> schemas.Routine:
    """Convert Routine entity to Routine schema."""
    return schemas.Routine(**asdict(routine))
