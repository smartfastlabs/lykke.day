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
from .message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from .notifications import (
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from .task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)

__all__ = [
    "CreateAdhocTaskCommand",
    "CreateAdhocTaskHandler",
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
    "RecordRoutineActionCommand",
    "RecordRoutineActionHandler",
    "RecordTaskActionCommand",
    "RecordTaskActionHandler",
    "RescheduleDayCommand",
    "RescheduleDayHandler",
    "ScheduleDayCommand",
    "ScheduleDayHandler",
    "SmartNotificationCommand",
    "SmartNotificationHandler",
    "SyncAllCalendarsCommand",
    "SyncAllCalendarsHandler",
    "SyncCalendarCommand",
    "SyncCalendarHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
]
