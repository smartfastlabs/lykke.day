"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .alarm import AlarmSchema
from .calendar import (
    CalendarCreateSchema,
    CalendarSchema,
    SyncSubscriptionSchema,
    CalendarUpdateSchema,
)
from .calendar_entry_series import (
    CalendarEntrySeriesSchema,
    CalendarEntrySeriesUpdateSchema,
)
from .calendar_entry import CalendarEntrySchema
from .day import DaySchema, DayUpdateSchema
from .day_context import DayContextSchema
from .day_template import (
    DayTemplateCreateSchema,
    DayTemplateRoutineCreateSchema,
    DayTemplateSchema,
    DayTemplateTimeBlockCreateSchema,
    DayTemplateTimeBlockSchema,
    DayTemplateUpdateSchema,
)
from .pagination import PagedResponseSchema
from .query import QuerySchema
from .user import (
    UserSchema,
    UserSettingsSchema,
    UserSettingsUpdateSchema,
    UserUpdateSchema,
)
from .push_subscription import (
    PushSubscriptionCreateSchema,
    PushSubscriptionKeysSchema,
    PushSubscriptionSchema,
    PushSubscriptionUpdateSchema,
)
from .routine import (
    RoutineCreateSchema,
    RoutineSchema,
    RoutineTaskCreateSchema,
    RoutineTaskUpdateSchema,
    RoutineUpdateSchema,
)
from .task import TaskScheduleSchema, TaskSchema
from .task_definition import (
    TaskDefinitionCreateSchema,
    TaskDefinitionSchema,
    TaskDefinitionUpdateSchema,
)
from .time_block_definition import (
    TimeBlockDefinitionCreateSchema,
    TimeBlockDefinitionSchema,
    TimeBlockDefinitionUpdateSchema,
)

# Rebuild models with forward references after all classes are defined
CalendarCreateSchema.model_rebuild()
CalendarSchema.model_rebuild()
SyncSubscriptionSchema.model_rebuild()
CalendarEntrySchema.model_rebuild()
CalendarUpdateSchema.model_rebuild()
CalendarEntrySeriesSchema.model_rebuild()
CalendarEntrySeriesUpdateSchema.model_rebuild()
DaySchema.model_rebuild()
DayTemplateCreateSchema.model_rebuild()
DayTemplateRoutineCreateSchema.model_rebuild()
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
UserSchema.model_rebuild()
UserSettingsSchema.model_rebuild()
UserSettingsUpdateSchema.model_rebuild()
UserUpdateSchema.model_rebuild()
PushSubscriptionCreateSchema.model_rebuild()
PushSubscriptionKeysSchema.model_rebuild()
PushSubscriptionSchema.model_rebuild()
PushSubscriptionUpdateSchema.model_rebuild()
TimeBlockDefinitionCreateSchema.model_rebuild()
TimeBlockDefinitionSchema.model_rebuild()
TimeBlockDefinitionUpdateSchema.model_rebuild()

__all__ = [
    "ActionSchema",
    "AlarmSchema",
    "CalendarEntrySchema",
    "CalendarEntrySeriesSchema",
    "CalendarCreateSchema",
    "CalendarSchema",
    "SyncSubscriptionSchema",
    "CalendarUpdateSchema",
    "CalendarEntrySeriesUpdateSchema",
    "DayContextSchema",
    "DaySchema",
    "DayTemplateCreateSchema",
    "DayTemplateRoutineCreateSchema",
    "DayTemplateSchema",
    "DayTemplateTimeBlockCreateSchema",
    "DayTemplateTimeBlockSchema",
    "DayTemplateUpdateSchema",
    "DayUpdateSchema",
    "PagedResponseSchema",
    "QuerySchema",
    "PushSubscriptionCreateSchema",
    "PushSubscriptionKeysSchema",
    "PushSubscriptionSchema",
    "PushSubscriptionUpdateSchema",
    "RoutineCreateSchema",
    "RoutineSchema",
    "RoutineTaskCreateSchema",
    "RoutineTaskUpdateSchema",
    "RoutineUpdateSchema",
    "TaskDefinitionCreateSchema",
    "TaskDefinitionSchema",
    "TaskDefinitionUpdateSchema",
    "TaskScheduleSchema",
    "TaskSchema",
    "TimeBlockDefinitionCreateSchema",
    "TimeBlockDefinitionSchema",
    "TimeBlockDefinitionUpdateSchema",
    "UserSchema",
    "UserSettingsSchema",
    "UserSettingsUpdateSchema",
    "UserUpdateSchema",
]
