"""Command handlers for state-changing operations.

Command handlers execute operations that change state, persist changes, and return results.
"""

from .calendar import (
    SyncAllCalendarsCommand,
    SyncAllCalendarsHandler,
    SyncCalendarCommand,
    SyncCalendarHandler,
)
from .day import (
    RescheduleDayCommand,
    RescheduleDayHandler,
    ScheduleDayCommand,
    ScheduleDayHandler,
    UpdateDayCommand,
    UpdateDayHandler,
)
from .task import (
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)

__all__ = [
    "RecordRoutineActionCommand",
    "RecordRoutineActionHandler",
    "RecordTaskActionCommand",
    "RecordTaskActionHandler",
    "RescheduleDayCommand",
    "RescheduleDayHandler",
    "ScheduleDayCommand",
    "ScheduleDayHandler",
    "SyncAllCalendarsCommand",
    "SyncAllCalendarsHandler",
    "SyncCalendarCommand",
    "SyncCalendarHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
]
