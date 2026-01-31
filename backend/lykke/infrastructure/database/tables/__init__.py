"""SQLAlchemy ORM table definitions."""

from .audit_logs import AuditLog
from .auth_tokens import AuthToken
from .base import Base, metadata
from .bot_personalities import BotPersonality
from .brain_dumps import BrainDump
from .calendar_entries import CalendarEntry
from .calendar_entry_series import CalendarEntrySeries
from .calendars import Calendar
from .day_templates import DayTemplate
from .days import Day
from .factoids import Factoid
from .messages import Message
from .push_notifications import PushNotification
from .push_subscriptions import PushSubscription
from .routine_definitions import RoutineDefinition
from .routines import Routine
from .tactics import Tactic
from .task_definitions import TaskDefinition
from .tasks import Task
from .time_block_definitions import TimeBlockDefinition
from .trigger_tactics import TriggerTactic
from .triggers import Trigger
from .usecase_config import UseCaseConfig
from .users import User

# Export table objects for Core-style queries
audit_logs_tbl = AuditLog.__table__
auth_tokens_tbl = AuthToken.__table__
bot_personalities_tbl = BotPersonality.__table__
brain_dumps_tbl = BrainDump.__table__
calendar_entries_tbl = CalendarEntry.__table__
calendar_entry_series_tbl = CalendarEntrySeries.__table__
calendars_tbl = Calendar.__table__
day_templates_tbl = DayTemplate.__table__
days_tbl = Day.__table__
factoids_tbl = Factoid.__table__
messages_tbl = Message.__table__
push_notifications_tbl = PushNotification.__table__
push_subscriptions_tbl = PushSubscription.__table__
routines_tbl = Routine.__table__
routine_definitions_tbl = RoutineDefinition.__table__
task_definitions_tbl = TaskDefinition.__table__
tactics_tbl = Tactic.__table__
trigger_tactics_tbl = TriggerTactic.__table__
triggers_tbl = Trigger.__table__
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
    "BrainDump",
    "Calendar",
    "CalendarEntry",
    "CalendarEntrySeries",
    "Day",
    "DayTemplate",
    "Factoid",
    "Message",
    "PushNotification",
    "PushSubscription",
    "Routine",
    "RoutineDefinition",
    "Task",
    "Tactic",
    "TaskDefinition",
    "Trigger",
    "TriggerTactic",
    "TimeBlockDefinition",
    "UseCaseConfig",
    "User",
    # Table objects (for Core-style queries)
    "audit_logs_tbl",
    "auth_tokens_tbl",
    "bot_personalities_tbl",
    "brain_dumps_tbl",
    "calendar_entries_tbl",
    "calendar_entry_series_tbl",
    "calendars_tbl",
    "day_templates_tbl",
    "days_tbl",
    "factoids_tbl",
    "messages_tbl",
    "metadata",
    "push_notifications_tbl",
    "push_subscriptions_tbl",
    "routines_tbl",
    "routine_definitions_tbl",
    "task_definitions_tbl",
    "tactics_tbl",
    "trigger_tactics_tbl",
    "triggers_tbl",
    "tasks_tbl",
    "time_block_definitions_tbl",
    "usecase_configs_tbl",
    "users_tbl",
]
