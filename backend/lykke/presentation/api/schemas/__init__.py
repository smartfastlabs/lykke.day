"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .auditable import AuditableSchema
from .audit_log import AuditLogSchema
from .base_personality import BasePersonalitySchema
from .bot_personality import BotPersonalitySchema
from .calendar import (
    CalendarCreateSchema,
    CalendarSchema,
    CalendarUpdateSchema,
    SyncSubscriptionSchema,
)
from .calendar_entry import CalendarEntrySchema
from .calendar_entry_series import (
    CalendarEntrySeriesSchema,
    CalendarEntrySeriesUpdateSchema,
)
from .conversation import ConversationSchema
from .brain_dump import BrainDumpItemSchema
from .day import DaySchema, DayUpdateSchema
from .day_context import DayContextSchema
from .high_level_plan import HighLevelPlanSchema
from .factoid import FactoidSchema
from .reminder import ReminderSchema
from .day_template import (
    DayTemplateCreateSchema,
    DayTemplateRoutineCreateSchema,
    DayTemplateSchema,
    DayTemplateTimeBlockCreateSchema,
    DayTemplateTimeBlockSchema,
    DayTemplateUpdateSchema,
)
from .message import MessageSchema, SendMessageRequestSchema, SendMessageResponseSchema
from .pagination import PagedResponseSchema
from .push_subscription import (
    PushSubscriptionCreateSchema,
    PushSubscriptionKeysSchema,
    PushSubscriptionSchema,
    PushSubscriptionUpdateSchema,
)
from .query import QuerySchema
from .routine import (
    RoutineCreateSchema,
    RoutineSchema,
    RoutineTaskCreateSchema,
    RoutineTaskUpdateSchema,
    RoutineUpdateSchema,
)
from .task import AdhocTaskCreateSchema, TaskScheduleSchema, TaskSchema
from .task_definition import (
    TaskDefinitionCreateSchema,
    TaskDefinitionSchema,
    TaskDefinitionUpdateSchema,
)
from .usecase_config import (
    NotificationUseCaseConfigSchema,
    UseCaseConfigCreateSchema,
    UseCaseConfigSchema,
)
from .time_block_definition import (
    TimeBlockDefinitionCreateSchema,
    TimeBlockDefinitionSchema,
    TimeBlockDefinitionUpdateSchema,
)
from .user import (
    UserSchema,
    UserSettingsSchema,
    UserSettingsUpdateSchema,
    UserUpdateSchema,
)
from .websocket_message import (
    EntityChangeSchema,
    WebSocketAuditLogEventSchema,
    WebSocketConnectionAckSchema,
    WebSocketErrorSchema,
    WebSocketMessageEventSchema,
    WebSocketSyncRequestSchema,
    WebSocketSyncResponseSchema,
    WebSocketUserMessageSchema,
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
HighLevelPlanSchema.model_rebuild()
TaskSchema.model_rebuild()
AdhocTaskCreateSchema.model_rebuild()
TaskDefinitionUpdateSchema.model_rebuild()
DayContextSchema.model_rebuild()
ReminderSchema.model_rebuild()
BrainDumpItemSchema.model_rebuild()
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
ConversationSchema.model_rebuild()
MessageSchema.model_rebuild()
SendMessageRequestSchema.model_rebuild()
SendMessageResponseSchema.model_rebuild()
BasePersonalitySchema.model_rebuild()
WebSocketUserMessageSchema.model_rebuild()
WebSocketMessageEventSchema.model_rebuild()
WebSocketAuditLogEventSchema.model_rebuild()
WebSocketConnectionAckSchema.model_rebuild()
WebSocketErrorSchema.model_rebuild()
EntityChangeSchema.model_rebuild()
WebSocketSyncRequestSchema.model_rebuild()
WebSocketSyncResponseSchema.model_rebuild()

__all__ = [
    "ActionSchema",
    "AuditableSchema",
    "AuditLogSchema",
    "BasePersonalitySchema",
    "BotPersonalitySchema",
    "CalendarCreateSchema",
    "CalendarEntrySchema",
    "CalendarEntrySeriesSchema",
    "CalendarEntrySeriesUpdateSchema",
    "CalendarSchema",
    "CalendarUpdateSchema",
    "ConversationSchema",
    "BrainDumpItemSchema",
    "DayContextSchema",
    "DaySchema",
    "FactoidSchema",
    "HighLevelPlanSchema",
    "ReminderSchema",
    "DayTemplateCreateSchema",
    "DayTemplateRoutineCreateSchema",
    "DayTemplateSchema",
    "DayTemplateTimeBlockCreateSchema",
    "DayTemplateTimeBlockSchema",
    "DayTemplateUpdateSchema",
    "DayUpdateSchema",
    "MessageSchema",
    "PagedResponseSchema",
    "PushSubscriptionCreateSchema",
    "PushSubscriptionKeysSchema",
    "PushSubscriptionSchema",
    "PushSubscriptionUpdateSchema",
    "QuerySchema",
    "RoutineCreateSchema",
    "RoutineSchema",
    "RoutineTaskCreateSchema",
    "RoutineTaskUpdateSchema",
    "RoutineUpdateSchema",
    "SendMessageRequestSchema",
    "SendMessageResponseSchema",
    "SyncSubscriptionSchema",
    "TaskDefinitionCreateSchema",
    "TaskDefinitionSchema",
    "TaskDefinitionUpdateSchema",
    "TaskScheduleSchema",
    "TaskSchema",
    "AdhocTaskCreateSchema",
    "NotificationUseCaseConfigSchema",
    "UseCaseConfigCreateSchema",
    "UseCaseConfigSchema",
    "TimeBlockDefinitionCreateSchema",
    "TimeBlockDefinitionSchema",
    "TimeBlockDefinitionUpdateSchema",
    "UserSchema",
    "UserSettingsSchema",
    "UserSettingsUpdateSchema",
    "UserUpdateSchema",
    "EntityChangeSchema",
    "WebSocketAuditLogEventSchema",
    "WebSocketConnectionAckSchema",
    "WebSocketErrorSchema",
    "WebSocketMessageEventSchema",
    "WebSocketSyncRequestSchema",
    "WebSocketSyncResponseSchema",
    "WebSocketUserMessageSchema",
]
