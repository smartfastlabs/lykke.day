"""Mapper functions to convert domain entities to API schemas."""

from planned.domain import entities, value_objects

from .action import ActionSchema
from .alarm import AlarmSchema
from .calendar_entry import CalendarEntrySchema
from .day import DaySchema
from .day_context import DayContextSchema
from .day_template import DayTemplateSchema
from .message import MessageSchema
from .person import PersonSchema
from .push_subscription import PushSubscriptionSchema
from .routine import RoutineSchema
from .task import TaskSchema, TaskScheduleSchema
from .task_definition import TaskDefinitionSchema


def map_action_to_schema(action: entities.Action) -> ActionSchema:
    """Convert Action entity to ActionSchema."""
    return ActionSchema.model_validate(action, from_attributes=True)


def map_alarm_to_schema(alarm: entities.Alarm) -> AlarmSchema:
    """Convert Alarm entity to AlarmSchema."""
    return AlarmSchema.model_validate(alarm, from_attributes=True)


def map_person_to_schema(person: entities.Person) -> PersonSchema:
    """Convert Person entity to PersonSchema."""
    return PersonSchema.model_validate(person, from_attributes=True)


def map_task_definition_to_schema(
    task_definition: entities.TaskDefinition,
) -> TaskDefinitionSchema:
    """Convert TaskDefinition entity to TaskDefinitionSchema."""
    return TaskDefinitionSchema.model_validate(
        task_definition, from_attributes=True
    )


def map_task_schedule_to_schema(
    schedule: value_objects.TaskSchedule | None,
) -> TaskScheduleSchema | None:
    """Convert TaskSchedule value object to TaskScheduleSchema."""
    if schedule is None:
        return None
    # TaskSchedule is already a Pydantic model, so we can validate it directly
    return TaskScheduleSchema.model_validate(schedule, from_attributes=True)


def map_task_to_schema(task: entities.Task) -> TaskSchema:
    """Convert Task entity to TaskSchema."""
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
    template: entities.DayTemplate,
) -> DayTemplateSchema:
    """Convert DayTemplate entity to DayTemplateSchema."""
    alarm_schema = (
        map_alarm_to_schema(template.alarm) if template.alarm else None
    )

    return DayTemplateSchema(
        id=template.id,
        user_id=template.user_id,
        slug=template.slug,
        alarm=alarm_schema,
        icon=template.icon,
        routine_ids=template.routine_ids,
    )


def map_day_to_schema(day: entities.Day) -> DaySchema:
    """Convert Day entity to DaySchema."""
    alarm_schema = map_alarm_to_schema(day.alarm) if day.alarm else None
    template_schema = (
        map_day_template_to_schema(day.template) if day.template else None
    )

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
    entry: entities.CalendarEntry,
) -> CalendarEntrySchema:
    """Convert CalendarEntry entity to CalendarEntrySchema."""
    person_schemas = [map_person_to_schema(person) for person in entry.people]
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
        people=person_schemas,
        actions=action_schemas,
        date=entry.date,  # Computed field
    )


def map_message_to_schema(message: entities.Message) -> MessageSchema:
    """Convert Message entity to MessageSchema."""
    return MessageSchema(
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
) -> DayContextSchema:
    """Convert DayContext value object to DayContextSchema."""
    day_schema = map_day_to_schema(context.day)
    calendar_entry_schemas = [
        map_calendar_entry_to_schema(entry) for entry in context.calendar_entries
    ]
    task_schemas = [map_task_to_schema(task) for task in context.tasks]
    message_schemas = [
        map_message_to_schema(message) for message in context.messages
    ]

    return DayContextSchema(
        day=day_schema,
        calendar_entries=calendar_entry_schemas,
        tasks=task_schemas,
        messages=message_schemas,
    )


def map_push_subscription_to_schema(
    subscription: entities.PushSubscription,
) -> PushSubscriptionSchema:
    """Convert PushSubscription entity to PushSubscriptionSchema."""
    return PushSubscriptionSchema.model_validate(
        subscription, from_attributes=True
    )


def map_routine_to_schema(routine: entities.Routine) -> RoutineSchema:
    """Convert Routine entity to RoutineSchema."""
    return RoutineSchema.model_validate(routine, from_attributes=True)

