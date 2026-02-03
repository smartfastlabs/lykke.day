"""Command handlers for state-changing operations.

Command handlers execute operations that change state, persist changes, and return results.
"""

from .brain_dump import (
    CreateBrainDumpCommand,
    CreateBrainDumpHandler,
    DeleteBrainDumpCommand,
    DeleteBrainDumpHandler,
    ProcessBrainDumpCommand,
    ProcessBrainDumpHandler,
    UpdateBrainDumpStatusCommand,
    UpdateBrainDumpStatusHandler,
    UpdateBrainDumpTypeCommand,
    UpdateBrainDumpTypeHandler,
)
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
from .google import (
    HandleGoogleLoginCallbackCommand,
    HandleGoogleLoginCallbackHandler,
    HandleGoogleLoginCallbackResult,
)
from .message import (
    ProcessInboundSmsCommand,
    ProcessInboundSmsHandler,
    ReceiveSmsMessageCommand,
    ReceiveSmsMessageHandler,
)
from .notifications import (
    CalendarEntryNotificationCommand,
    CalendarEntryNotificationHandler,
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from .task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    DeleteTaskCommand,
    DeleteTaskHandler,
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
    RescheduleTaskCommand,
    RescheduleTaskHandler,
)
from .timing_status import EvaluateTimingStatusCommand, EvaluateTimingStatusHandler

__all__ = [
    "CreateAdhocTaskCommand",
    "CreateAdhocTaskHandler",
    "CreateBrainDumpCommand",
    "CreateBrainDumpHandler",
    "DeleteBrainDumpCommand",
    "DeleteBrainDumpHandler",
    "DeleteTaskCommand",
    "DeleteTaskHandler",
    "EvaluateTimingStatusCommand",
    "EvaluateTimingStatusHandler",
    "HandleGoogleLoginCallbackCommand",
    "HandleGoogleLoginCallbackHandler",
    "HandleGoogleLoginCallbackResult",
    "ProcessBrainDumpCommand",
    "ProcessBrainDumpHandler",
    "ProcessInboundSmsCommand",
    "ProcessInboundSmsHandler",
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
    "RecordRoutineActionCommand",
    "RecordRoutineActionHandler",
    "RecordTaskActionCommand",
    "RecordTaskActionHandler",
    "RescheduleTaskCommand",
    "RescheduleTaskHandler",
    "RescheduleDayCommand",
    "RescheduleDayHandler",
    "ScheduleDayCommand",
    "ScheduleDayHandler",
    "SmartNotificationCommand",
    "SmartNotificationHandler",
    "CalendarEntryNotificationCommand",
    "CalendarEntryNotificationHandler",
    "SyncAllCalendarsCommand",
    "SyncAllCalendarsHandler",
    "SyncCalendarCommand",
    "SyncCalendarHandler",
    "UpdateBrainDumpStatusCommand",
    "UpdateBrainDumpStatusHandler",
    "UpdateBrainDumpTypeCommand",
    "UpdateBrainDumpTypeHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
]
