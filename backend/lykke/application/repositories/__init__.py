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
from .user_repository import (
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)

__all__ = [
    # Read-only protocols
    "AuthTokenRepositoryReadOnlyProtocol",
    "AuthTokenRepositoryProtocol",
    "CalendarEntryRepositoryReadOnlyProtocol",
    "CalendarEntryRepositoryProtocol",
    "CalendarRepositoryReadOnlyProtocol",
    "CalendarRepositoryProtocol",
    "DayRepositoryReadOnlyProtocol",
    "DayRepositoryProtocol",
    "DayTemplateRepositoryReadOnlyProtocol",
    "DayTemplateRepositoryProtocol",
    "PushSubscriptionRepositoryReadOnlyProtocol",
    "PushSubscriptionRepositoryProtocol",
    "RoutineRepositoryReadOnlyProtocol",
    "RoutineRepositoryProtocol",
    "TaskDefinitionRepositoryReadOnlyProtocol",
    "TaskDefinitionRepositoryProtocol",
    "TaskRepositoryReadOnlyProtocol",
    "TaskRepositoryProtocol",
    "UserRepositoryReadOnlyProtocol",
    "UserRepositoryProtocol",
    # Read-write protocols
    "AuthTokenRepositoryReadWriteProtocol",
    "CalendarEntryRepositoryReadWriteProtocol",
    "CalendarRepositoryReadWriteProtocol",
    "DayRepositoryReadWriteProtocol",
    "DayTemplateRepositoryReadWriteProtocol",
    "PushSubscriptionRepositoryReadWriteProtocol",
    "RoutineRepositoryReadWriteProtocol",
    "TaskDefinitionRepositoryReadWriteProtocol",
    "TaskRepositoryReadWriteProtocol",
    "UserRepositoryReadWriteProtocol",
]

# Backward-compatibility aliases (old protocol names)
AuthTokenRepositoryProtocol = AuthTokenRepositoryReadOnlyProtocol
CalendarEntryRepositoryProtocol = CalendarEntryRepositoryReadOnlyProtocol
CalendarRepositoryProtocol = CalendarRepositoryReadOnlyProtocol
DayRepositoryProtocol = DayRepositoryReadOnlyProtocol
DayTemplateRepositoryProtocol = DayTemplateRepositoryReadOnlyProtocol
PushSubscriptionRepositoryProtocol = PushSubscriptionRepositoryReadOnlyProtocol
RoutineRepositoryProtocol = RoutineRepositoryReadOnlyProtocol
TaskDefinitionRepositoryProtocol = TaskDefinitionRepositoryReadOnlyProtocol
TaskRepositoryProtocol = TaskRepositoryReadOnlyProtocol
UserRepositoryProtocol = UserRepositoryReadOnlyProtocol
