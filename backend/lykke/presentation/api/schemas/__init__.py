"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import ActionSchema
from .alarm import AlarmPresetSchema, AlarmSchema
from .audit_log import AuditLogSchema
from .auditable import AuditableSchema
from .base_personality import BasePersonalitySchema
from .bot_personality import BotPersonalitySchema
from .brain_dump import BrainDumpCreateSchema, BrainDumpSchema, BrainDumpUpdateSchema
from .calendar import (
    CalendarCreateSchema,
    CalendarSchema,
    CalendarUpdateSchema,
    SyncSubscriptionSchema,
)
from .calendar_entry import CalendarEntrySchema, CalendarEntryUpdateSchema
from .calendar_entry_series import (
    CalendarEntrySeriesSchema,
    CalendarEntrySeriesUpdateSchema,
)
from .day import DaySchema, DayUpdateSchema
from .day_context import DayContextSchema
from .day_template import (
    DayTemplateCreateSchema,
    DayTemplateRoutineDefinitionCreateSchema,
    DayTemplateSchema,
    DayTemplateTimeBlockCreateSchema,
    DayTemplateTimeBlockSchema,
    DayTemplateUpdateSchema,
)
from .early_access import EarlyAccessRequestSchema, StatusResponseSchema
from .factoid import FactoidCreateSchema, FactoidSchema, FactoidUpdateSchema
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
from .routine import RoutineSchema
from .routine_definition import (
    RoutineDefinitionCreateSchema,
    RoutineDefinitionSchema,
    RoutineDefinitionTaskCreateSchema,
    RoutineDefinitionTaskUpdateSchema,
    RoutineDefinitionUpdateSchema,
    TimeWindowSchema,
)
from .tactic import TacticCreateSchema, TacticSchema, TacticUpdateSchema
from .task import AdhocTaskCreateSchema, TaskRescheduleSchema, TaskSchema
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
from .trigger import (
    TriggerCreateSchema,
    TriggerSchema,
    TriggerTacticsUpdateSchema,
    TriggerUpdateSchema,
)
from .usecase_config import (
    NotificationUseCaseConfigSchema,
    UseCaseConfigCreateSchema,
    UseCaseConfigSchema,
)
from .user import (
    CalendarEntryNotificationRuleSchema,
    CalendarEntryNotificationSettingsSchema,
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
CalendarEntryUpdateSchema.model_rebuild()
CalendarUpdateSchema.model_rebuild()
CalendarEntrySeriesSchema.model_rebuild()
CalendarEntrySeriesUpdateSchema.model_rebuild()
DaySchema.model_rebuild()
DayTemplateCreateSchema.model_rebuild()
DayTemplateRoutineDefinitionCreateSchema.model_rebuild()
DayTemplateSchema.model_rebuild()
DayTemplateUpdateSchema.model_rebuild()
DayUpdateSchema.model_rebuild()
HighLevelPlanSchema.model_rebuild()
TaskSchema.model_rebuild()
AdhocTaskCreateSchema.model_rebuild()
TaskRescheduleSchema.model_rebuild()
TaskDefinitionUpdateSchema.model_rebuild()
TacticSchema.model_rebuild()
DayContextSchema.model_rebuild()
AlarmSchema.model_rebuild()
AlarmPresetSchema.model_rebuild()
BrainDumpSchema.model_rebuild()
BrainDumpCreateSchema.model_rebuild()
BrainDumpUpdateSchema.model_rebuild()
RoutineDefinitionSchema.model_rebuild()
RoutineDefinitionTaskCreateSchema.model_rebuild()
RoutineDefinitionTaskUpdateSchema.model_rebuild()
TimeWindowSchema.model_rebuild()
RoutineDefinitionUpdateSchema.model_rebuild()
RoutineSchema.model_rebuild()
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
TriggerSchema.model_rebuild()
TriggerTacticsUpdateSchema.model_rebuild()
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
    "AlarmPresetSchema",
    "AlarmSchema",
    "AuditLogSchema",
    "AuditableSchema",
    "BasePersonalitySchema",
    "BotPersonalitySchema",
    "BrainDumpCreateSchema",
    "BrainDumpSchema",
    "BrainDumpUpdateSchema",
    "CalendarCreateSchema",
    "CalendarEntrySchema",
    "CalendarEntrySeriesSchema",
    "CalendarEntrySeriesUpdateSchema",
    "CalendarEntryUpdateSchema",
    "CalendarEntryNotificationRuleSchema",
    "CalendarEntryNotificationSettingsSchema",
    "CalendarSchema",
    "CalendarUpdateSchema",
    "DayContextSchema",
    "DaySchema",
    "DayTemplateCreateSchema",
    "DayTemplateRoutineDefinitionCreateSchema",
    "DayTemplateSchema",
    "DayTemplateTimeBlockCreateSchema",
    "DayTemplateTimeBlockSchema",
    "DayTemplateUpdateSchema",
    "DayUpdateSchema",
    "EarlyAccessRequestSchema",
    "EntityChangeSchema",
    "FactoidCreateSchema",
    "FactoidSchema",
    "FactoidUpdateSchema",
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
    "RoutineDefinitionCreateSchema",
    "RoutineDefinitionSchema",
    "RoutineDefinitionTaskCreateSchema",
    "RoutineDefinitionTaskUpdateSchema",
    "RoutineDefinitionUpdateSchema",
    "RoutineSchema",
    "SendMessageRequestSchema",
    "SendMessageResponseSchema",
    "StatusResponseSchema",
    "SyncSubscriptionSchema",
    "TacticCreateSchema",
    "TacticSchema",
    "TacticUpdateSchema",
    "TaskDefinitionCreateSchema",
    "TaskDefinitionSchema",
    "TaskDefinitionUpdateSchema",
    "TaskRescheduleSchema",
    "TaskSchema",
    "TimeBlockDefinitionCreateSchema",
    "TimeBlockDefinitionSchema",
    "TimeBlockDefinitionUpdateSchema",
    "TimeWindowSchema",
    "TriggerCreateSchema",
    "TriggerSchema",
    "TriggerTacticsUpdateSchema",
    "TriggerUpdateSchema",
    "UseCaseConfigCreateSchema",
    "UseCaseConfigSchema",
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
