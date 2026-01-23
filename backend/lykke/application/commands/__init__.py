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
from .notifications import (
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from .message import (
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
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
    "RecordRoutineActionCommand",
    "RecordRoutineActionHandler",
    "RecordTaskActionCommand",
    "RecordTaskActionHandler",
    "CreateAdhocTaskCommand",
    "CreateAdhocTaskHandler",
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
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
]
