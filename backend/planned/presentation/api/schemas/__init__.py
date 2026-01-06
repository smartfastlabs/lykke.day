"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .alarm import AlarmSchema
from .calendar import CalendarSchema, CalendarUpdateSchema
from .calendar_entry import CalendarEntrySchema
from .day import DaySchema, DayUpdateSchema
from .day_context import DayContextSchema
from .day_template import DayTemplateSchema, DayTemplateUpdateSchema
from .push_subscription import PushSubscriptionSchema
from .routine import (
    RoutineCreateSchema,
    RoutineSchema,
    RoutineTaskCreateSchema,
    RoutineTaskUpdateSchema,
    RoutineUpdateSchema,
)
from .task import TaskScheduleSchema, TaskSchema
from .task_definition import TaskDefinitionSchema, TaskDefinitionUpdateSchema

# Rebuild models with forward references after all classes are defined
CalendarSchema.model_rebuild()
CalendarEntrySchema.model_rebuild()
CalendarUpdateSchema.model_rebuild()
DaySchema.model_rebuild()
DayTemplateSchema.model_rebuild()
DayTemplateUpdateSchema.model_rebuild()
DayUpdateSchema.model_rebuild()
TaskSchema.model_rebuild()
TaskDefinitionUpdateSchema.model_rebuild()
DayContextSchema.model_rebuild()
RoutineSchema.model_rebuild()
RoutineTaskCreateSchema.model_rebuild()
RoutineTaskUpdateSchema.model_rebuild()
RoutineUpdateSchema.model_rebuild()

__all__ = [
    "ActionSchema",
    "AlarmSchema",
    "CalendarEntrySchema",
    "CalendarSchema",
    "CalendarUpdateSchema",
    "DayContextSchema",
    "DaySchema",
    "DayTemplateSchema",
    "DayTemplateUpdateSchema",
    "DayUpdateSchema",
    "PushSubscriptionSchema",
    "RoutineCreateSchema",
    "RoutineSchema",
    "RoutineTaskCreateSchema",
    "RoutineTaskUpdateSchema",
    "RoutineUpdateSchema",
    "TaskDefinitionSchema",
    "TaskDefinitionUpdateSchema",
    "TaskScheduleSchema",
    "TaskSchema",
]
