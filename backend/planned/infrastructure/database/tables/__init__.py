"""SQLAlchemy ORM table definitions."""

from .auth_tokens import AuthToken
from .base import Base, metadata
from .calendars import Calendar
from .day_templates import DayTemplate
from .days import Day
from .events import Event
from .messages import Message
from .push_subscriptions import PushSubscription
from .routines import Routine
from .task_definitions import TaskDefinition
from .tasks import Task
from .users import User

# Export table objects for Core-style queries
auth_tokens_tbl = AuthToken.__table__
calendars_tbl = Calendar.__table__
day_templates_tbl = DayTemplate.__table__
days_tbl = Day.__table__
events_tbl = Event.__table__
messages_tbl = Message.__table__
push_subscriptions_tbl = PushSubscription.__table__
routines_tbl = Routine.__table__
task_definitions_tbl = TaskDefinition.__table__
tasks_tbl = Task.__table__
users_tbl = User.__table__

__all__ = [
    # Base and metadata
    "Base",
    "metadata",
    # ORM Models
    "AuthToken",
    "Calendar",
    "Day",
    "DayTemplate",
    "Event",
    "Message",
    "PushSubscription",
    "Routine",
    "Task",
    "TaskDefinition",
    "User",
    # Table objects (for Core-style queries)
    "auth_tokens_tbl",
    "calendars_tbl",
    "day_templates_tbl",
    "days_tbl",
    "events_tbl",
    "messages_tbl",
    "push_subscriptions_tbl",
    "routines_tbl",
    "task_definitions_tbl",
    "tasks_tbl",
    "users_tbl",
]
