"""Repository protocol interfaces for the application layer.

These protocols define the interface that repositories must implement,
allowing services to depend on abstractions rather than concrete implementations.
"""

from .audit_log_repository import AuditLogRepositoryReadOnlyProtocol
from .auth_token_repository import (
    AuthTokenRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadWriteProtocol,
)
from .bot_personality_repository import (
    BotPersonalityRepositoryReadOnlyProtocol,
    BotPersonalityRepositoryReadWriteProtocol,
)
from .calendar_entry_repository import (
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadWriteProtocol,
)
from .calendar_entry_series_repository import (
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
    CalendarEntrySeriesRepositoryReadWriteProtocol,
)
from .calendar_repository import (
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
)
from .conversation_repository import (
    ConversationRepositoryReadOnlyProtocol,
    ConversationRepositoryReadWriteProtocol,
)
from .day_repository import (
    DayRepositoryReadOnlyProtocol,
    DayRepositoryReadWriteProtocol,
)
from .day_template_repository import (
    DayTemplateRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadWriteProtocol,
)
from .factoid_repository import (
    FactoidRepositoryReadOnlyProtocol,
    FactoidRepositoryReadWriteProtocol,
)
from .message_repository import (
    MessageRepositoryReadOnlyProtocol,
    MessageRepositoryReadWriteProtocol,
)
from .push_notification_repository import (
    PushNotificationRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadWriteProtocol,
)
from .push_subscription_repository import (
    PushSubscriptionRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadWriteProtocol,
)
from .routine_repository import (
    RoutineRepositoryReadOnlyProtocol,
    RoutineRepositoryReadWriteProtocol,
)
from .task_definition_repository import (
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadWriteProtocol,
)
from .task_repository import (
    TaskRepositoryReadOnlyProtocol,
    TaskRepositoryReadWriteProtocol,
)
from .time_block_definition_repository import (
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadWriteProtocol,
)
from .usecase_config_repository import (
    UseCaseConfigRepositoryReadOnlyProtocol,
    UseCaseConfigRepositoryReadWriteProtocol,
)
from .user_repository import (
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)

# Exported repository protocols (sorted alphabetically)
__all__ = [
    "AuditLogRepositoryReadOnlyProtocol",
    "AuthTokenRepositoryReadOnlyProtocol",
    "AuthTokenRepositoryReadWriteProtocol",
    "BotPersonalityRepositoryReadOnlyProtocol",
    "BotPersonalityRepositoryReadWriteProtocol",
    "CalendarEntryRepositoryReadOnlyProtocol",
    "CalendarEntryRepositoryReadWriteProtocol",
    "CalendarEntrySeriesRepositoryReadOnlyProtocol",
    "CalendarEntrySeriesRepositoryReadWriteProtocol",
    "CalendarRepositoryReadOnlyProtocol",
    "CalendarRepositoryReadWriteProtocol",
    "ConversationRepositoryReadOnlyProtocol",
    "ConversationRepositoryReadWriteProtocol",
    "DayRepositoryReadOnlyProtocol",
    "DayRepositoryReadWriteProtocol",
    "DayTemplateRepositoryReadOnlyProtocol",
    "DayTemplateRepositoryReadWriteProtocol",
    "FactoidRepositoryReadOnlyProtocol",
    "FactoidRepositoryReadWriteProtocol",
    "MessageRepositoryReadOnlyProtocol",
    "MessageRepositoryReadWriteProtocol",
    "PushNotificationRepositoryReadOnlyProtocol",
    "PushNotificationRepositoryReadWriteProtocol",
    "PushSubscriptionRepositoryReadOnlyProtocol",
    "PushSubscriptionRepositoryReadWriteProtocol",
    "RoutineRepositoryReadOnlyProtocol",
    "RoutineRepositoryReadWriteProtocol",
    "TaskDefinitionRepositoryReadOnlyProtocol",
    "TaskDefinitionRepositoryReadWriteProtocol",
    "TaskRepositoryReadOnlyProtocol",
    "TaskRepositoryReadWriteProtocol",
    "TimeBlockDefinitionRepositoryReadOnlyProtocol",
    "TimeBlockDefinitionRepositoryReadWriteProtocol",
    "UseCaseConfigRepositoryReadOnlyProtocol",
    "UseCaseConfigRepositoryReadWriteProtocol",
    "UserRepositoryReadOnlyProtocol",
    "UserRepositoryReadWriteProtocol",
]
