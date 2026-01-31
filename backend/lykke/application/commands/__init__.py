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
from .message import ReceiveSmsMessageCommand, ReceiveSmsMessageHandler
from .notifications import SmartNotificationCommand, SmartNotificationHandler
from .task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    DeleteTaskCommand,
    DeleteTaskHandler,
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
    RecordRoutineDefinitionActionCommand,
    RecordRoutineDefinitionActionHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
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
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
    "RecordRoutineActionCommand",
    "RecordRoutineActionHandler",
    "RecordRoutineDefinitionActionCommand",
    "RecordRoutineDefinitionActionHandler",
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
    "UpdateBrainDumpStatusCommand",
    "UpdateBrainDumpStatusHandler",
    "UpdateBrainDumpTypeCommand",
    "UpdateBrainDumpTypeHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
]
