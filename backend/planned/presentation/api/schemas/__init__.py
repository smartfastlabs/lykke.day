"""API response schemas (DTOs) for decoupling domain entities from presentation layer."""

from .action import Action
from .alarm import Alarm
from .calendar_entry import CalendarEntry
from .day import Day
from .day_context import DayContext
from .day_template import DayTemplate
from .message import Message
from .person import Person
from .push_subscription import PushSubscription
from .routine import Routine
from .task import Task, TaskSchedule
from .task_definition import TaskDefinition

# Rebuild models with forward references after all classes are defined
CalendarEntry.model_rebuild()
Day.model_rebuild()
DayTemplate.model_rebuild()
Task.model_rebuild()
DayContext.model_rebuild()

__all__ = [
    "Action",
    "Alarm",
    "CalendarEntry",
    "Day",
    "DayContext",
    "DayTemplate",
    "Message",
    "Person",
    "PushSubscription",
    "Routine",
    "Task",
    "TaskDefinition",
    "TaskSchedule",
]
