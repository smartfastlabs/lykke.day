"""Command handlers for state-changing operations.

Command handlers execute operations that change state, persist changes, and return results.
"""

from .calendar import (
    SyncAllCalendarsCommand,
    SyncAllCalendarsHandler,
    SyncCalendarCommand,
    SyncCalendarHandler,
)
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
from .google import (
    HandleGoogleLoginCallbackCommand,
    HandleGoogleLoginCallbackHandler,
    HandleGoogleLoginCallbackResult,
)
from .notifications import (
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from .task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    RecordRoutineDefinitionActionCommand,
    RecordRoutineDefinitionActionHandler,
    RecordRoutineActionCommand,
    RecordRoutineActionHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)

__all__ = [
    "CreateAdhocTaskCommand",
    "CreateAdhocTaskHandler",
    "CreateBrainDumpCommand",
    "CreateBrainDumpHandler",
    "DeleteBrainDumpCommand",
    "DeleteBrainDumpHandler",
    "ProcessBrainDumpCommand",
    "ProcessBrainDumpHandler",
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
    "HandleGoogleLoginCallbackCommand",
    "HandleGoogleLoginCallbackHandler",
    "HandleGoogleLoginCallbackResult",
    "RecordRoutineDefinitionActionCommand",
    "RecordRoutineDefinitionActionHandler",
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
    "UpdateBrainDumpStatusCommand",
    "UpdateBrainDumpStatusHandler",
    "UpdateBrainDumpTypeCommand",
    "UpdateBrainDumpTypeHandler",
]
