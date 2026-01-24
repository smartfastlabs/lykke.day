"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .audit_log import AuditLogSchema
from .auditable import AuditableSchema
from .base_personality import BasePersonalitySchema
from .bot_personality import BotPersonalitySchema
from .brain_dump import BrainDumpItemSchema
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
from .early_access import EarlyAccessRequestSchema, StatusResponseSchema
from .factoid import FactoidSchema
from .high_level_plan import HighLevelPlanSchema
from .message import MessageSchema, SendMessageRequestSchema, SendMessageResponseSchema
from .pagination import PagedResponseSchema
from .push_notification import PushNotificationSchema
from .push_subscription import (
    PushSubscriptionCreateSchema,
    PushSubscriptionKeysSchema,
    PushSubscriptionSchema,
    PushSubscriptionUpdateSchema,
)
from .query import QuerySchema
from .reminder import ReminderSchema
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
from .time_block_definition import (
    TimeBlockDefinitionCreateSchema,
    TimeBlockDefinitionSchema,
    TimeBlockDefinitionUpdateSchema,
)
from .usecase_config import (
    NotificationUseCaseConfigSchema,
    UseCaseConfigCreateSchema,
    UseCaseConfigSchema,
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
PushNotificationSchema.model_rebuild()
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
    "AdhocTaskCreateSchema",
    "AuditLogSchema",
    "AuditableSchema",
    "BasePersonalitySchema",
    "BotPersonalitySchema",
    "BrainDumpItemSchema",
    "CalendarCreateSchema",
    "CalendarEntrySchema",
    "CalendarEntrySeriesSchema",
    "CalendarEntrySeriesUpdateSchema",
    "CalendarSchema",
    "CalendarUpdateSchema",
    "ConversationSchema",
    "DayContextSchema",
    "DaySchema",
    "DayTemplateCreateSchema",
    "DayTemplateRoutineCreateSchema",
    "DayTemplateSchema",
    "DayTemplateTimeBlockCreateSchema",
    "DayTemplateTimeBlockSchema",
    "DayTemplateUpdateSchema",
    "DayUpdateSchema",
    "EarlyAccessRequestSchema",
    "EntityChangeSchema",
    "FactoidSchema",
    "HighLevelPlanSchema",
    "MessageSchema",
    "NotificationUseCaseConfigSchema",
    "PagedResponseSchema",
    "PushNotificationSchema",
    "PushSubscriptionCreateSchema",
    "PushSubscriptionKeysSchema",
    "PushSubscriptionSchema",
    "PushSubscriptionUpdateSchema",
    "QuerySchema",
    "ReminderSchema",
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
    "TimeBlockDefinitionCreateSchema",
    "TimeBlockDefinitionSchema",
    "TimeBlockDefinitionUpdateSchema",
    "UseCaseConfigCreateSchema",
    "UseCaseConfigSchema",
    "StatusResponseSchema",
    "UserSchema",
    "UserSettingsSchema",
    "UserSettingsUpdateSchema",
    "UserUpdateSchema",
    "WebSocketAuditLogEventSchema",
    "WebSocketConnectionAckSchema",
    "WebSocketErrorSchema",
    "WebSocketMessageEventSchema",
    "WebSocketSyncRequestSchema",
    "WebSocketSyncResponseSchema",
    "WebSocketUserMessageSchema",
]
