"""Repository protocol interfaces for the application layer.

These protocols define the interface that repositories must implement,
allowing services to depend on abstractions rather than concrete implementations.
"""

from .auth_token_repository import AuthTokenRepositoryProtocol
from .calendar_entry_repository import CalendarEntryRepositoryProtocol
from .calendar_repository import CalendarRepositoryProtocol
from .day_repository import DayRepositoryProtocol
from .day_template_repository import DayTemplateRepositoryProtocol
from .message_repository import MessageRepositoryProtocol
from .push_subscription_repository import PushSubscriptionRepositoryProtocol
from .routine_repository import RoutineRepositoryProtocol
from .task_definition_repository import TaskDefinitionRepositoryProtocol
from .task_repository import TaskRepositoryProtocol
from .user_repository import UserRepositoryProtocol

__all__ = [
    "AuthTokenRepositoryProtocol",
    "CalendarEntryRepositoryProtocol",
    "CalendarRepositoryProtocol",
    "DayRepositoryProtocol",
    "DayTemplateRepositoryProtocol",
    "MessageRepositoryProtocol",
    "PushSubscriptionRepositoryProtocol",
    "RoutineRepositoryProtocol",
    "TaskDefinitionRepositoryProtocol",
    "TaskRepositoryProtocol",
    "UserRepositoryProtocol",
]

