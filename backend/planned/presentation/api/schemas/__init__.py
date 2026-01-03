"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .alarm import AlarmSchema
from .calendar import CalendarSchema
from .calendar_entry import CalendarEntrySchema
from .day import DaySchema
from .day_context import DayContextSchema
from .day_template import DayTemplateSchema
from .message import MessageSchema
from .push_subscription import PushSubscriptionSchema
from .routine import RoutineSchema
from .task import TaskScheduleSchema, TaskSchema
from .task_definition import TaskDefinitionSchema

# Rebuild models with forward references after all classes are defined
CalendarSchema.model_rebuild()
CalendarEntrySchema.model_rebuild()
DaySchema.model_rebuild()
DayTemplateSchema.model_rebuild()
TaskSchema.model_rebuild()
DayContextSchema.model_rebuild()

__all__ = [
    "ActionSchema",
    "AlarmSchema",
    "CalendarEntrySchema",
    "CalendarSchema",
    "DayContextSchema",
    "DaySchema",
    "DayTemplateSchema",
    "MessageSchema",
    "PushSubscriptionSchema",
    "RoutineSchema",
    "TaskDefinitionSchema",
    "TaskScheduleSchema",
    "TaskSchema",
]
