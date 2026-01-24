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
    CreateBrainDumpItemCommand,
    CreateBrainDumpItemHandler,
    DeleteBrainDumpItemCommand,
    DeleteBrainDumpItemHandler,
    ProcessBrainDumpCommand,
    ProcessBrainDumpHandler,
    UpdateBrainDumpItemStatusCommand,
    UpdateBrainDumpItemStatusHandler,
    UpdateBrainDumpItemTypeCommand,
    UpdateBrainDumpItemTypeHandler,
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
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)

__all__ = [
    "CreateAdhocTaskCommand",
    "CreateAdhocTaskHandler",
    "CreateBrainDumpItemCommand",
    "CreateBrainDumpItemHandler",
    "DeleteBrainDumpItemCommand",
    "DeleteBrainDumpItemHandler",
    "ProcessBrainDumpCommand",
    "ProcessBrainDumpHandler",
    "ReceiveSmsMessageCommand",
    "ReceiveSmsMessageHandler",
    "HandleGoogleLoginCallbackCommand",
    "HandleGoogleLoginCallbackHandler",
    "HandleGoogleLoginCallbackResult",
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
    "UpdateDayCommand",
    "UpdateDayHandler",
    "UpdateBrainDumpItemStatusCommand",
    "UpdateBrainDumpItemStatusHandler",
    "UpdateBrainDumpItemTypeCommand",
    "UpdateBrainDumpItemTypeHandler",
]
