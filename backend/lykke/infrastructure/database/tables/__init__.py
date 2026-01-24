"""SQLAlchemy ORM table definitions."""

from .audit_logs import AuditLog
from .auth_tokens import AuthToken
from .base import Base, metadata
from .bot_personalities import BotPersonality
from .brain_dump_items import BrainDumpItem
from .calendar_entries import CalendarEntry
from .calendar_entry_series import CalendarEntrySeries
from .calendars import Calendar
from .conversations import Conversation
from .day_templates import DayTemplate
from .days import Day
from .factoids import Factoid
from .messages import Message
from .push_notifications import PushNotification
from .push_subscriptions import PushSubscription
from .routines import Routine
from .task_definitions import TaskDefinition
from .tasks import Task
from .time_block_definitions import TimeBlockDefinition
from .usecase_config import UseCaseConfig
from .users import User

# Export table objects for Core-style queries
audit_logs_tbl = AuditLog.__table__
auth_tokens_tbl = AuthToken.__table__
bot_personalities_tbl = BotPersonality.__table__
brain_dump_items_tbl = BrainDumpItem.__table__
calendar_entries_tbl = CalendarEntry.__table__
calendar_entry_series_tbl = CalendarEntrySeries.__table__
calendars_tbl = Calendar.__table__
conversations_tbl = Conversation.__table__
day_templates_tbl = DayTemplate.__table__
days_tbl = Day.__table__
factoids_tbl = Factoid.__table__
messages_tbl = Message.__table__
push_notifications_tbl = PushNotification.__table__
push_subscriptions_tbl = PushSubscription.__table__
routines_tbl = Routine.__table__
task_definitions_tbl = TaskDefinition.__table__
tasks_tbl = Task.__table__
time_block_definitions_tbl = TimeBlockDefinition.__table__
usecase_configs_tbl = UseCaseConfig.__table__
users_tbl = User.__table__

__all__ = [
    # ORM Models
    "AuditLog",
    "AuthToken",
    # Base and metadata
    "Base",
    "BotPersonality",
    "BrainDumpItem",
    "Calendar",
    "CalendarEntry",
    "CalendarEntrySeries",
    "Conversation",
    "Day",
    "DayTemplate",
    "Factoid",
    "Message",
    "PushNotification",
    "PushSubscription",
    "Routine",
    "Task",
    "TaskDefinition",
    "TimeBlockDefinition",
    "UseCaseConfig",
    "User",
    # Table objects (for Core-style queries)
    "audit_logs_tbl",
    "auth_tokens_tbl",
    "bot_personalities_tbl",
    "brain_dump_items_tbl",
    "calendar_entries_tbl",
    "calendar_entry_series_tbl",
    "calendars_tbl",
    "conversations_tbl",
    "day_templates_tbl",
    "days_tbl",
    "factoids_tbl",
    "messages_tbl",
    "metadata",
    "push_notifications_tbl",
    "push_subscriptions_tbl",
    "routines_tbl",
    "task_definitions_tbl",
    "tasks_tbl",
    "time_block_definitions_tbl",
    "usecase_configs_tbl",
    "users_tbl",
]
