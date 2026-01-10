"""Repository protocol interfaces for the application layer.

These protocols define the interface that repositories must implement,
allowing services to depend on abstractions rather than concrete implementations.
"""

from .auth_token_repository import (
    AuthTokenRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadWriteProtocol,
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
from .day_repository import (
    DayRepositoryReadOnlyProtocol,
    DayRepositoryReadWriteProtocol,
)
from .day_template_repository import (
    DayTemplateRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadWriteProtocol,
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
from .user_repository import (
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)

# Exported repository protocols (sorted alphabetically)
__all__ = [
    "AuthTokenRepositoryReadOnlyProtocol",
    "AuthTokenRepositoryReadWriteProtocol",
    "CalendarEntryRepositoryReadOnlyProtocol",
    "CalendarEntryRepositoryReadWriteProtocol",
    "CalendarEntrySeriesRepositoryReadOnlyProtocol",
    "CalendarEntrySeriesRepositoryReadWriteProtocol",
    "CalendarRepositoryReadOnlyProtocol",
    "CalendarRepositoryReadWriteProtocol",
    "DayRepositoryReadOnlyProtocol",
    "DayRepositoryReadWriteProtocol",
    "DayTemplateRepositoryReadOnlyProtocol",
    "DayTemplateRepositoryReadWriteProtocol",
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
    "UserRepositoryReadOnlyProtocol",
    "UserRepositoryReadWriteProtocol",
]
