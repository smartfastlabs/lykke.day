"""Day command handlers."""

from .add_alarm import AddAlarmToDayCommand, AddAlarmToDayHandler
from .add_reminder import AddReminderToDayCommand, AddReminderToDayHandler
from .add_routine_definition import (
    AddRoutineDefinitionToDayCommand,
    AddRoutineDefinitionToDayHandler,
)
from .remove_alarm import RemoveAlarmFromDayCommand, RemoveAlarmFromDayHandler
from .remove_reminder import RemoveReminderCommand, RemoveReminderHandler
from .reschedule_day import RescheduleDayCommand, RescheduleDayHandler
from .schedule_day import ScheduleDayCommand, ScheduleDayHandler
from .update_alarm_status import UpdateAlarmStatusCommand, UpdateAlarmStatusHandler
from .update_day import UpdateDayCommand, UpdateDayHandler
from .update_reminder_status import (
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)

__all__ = [
    "AddAlarmToDayCommand",
    "AddAlarmToDayHandler",
    "AddReminderToDayCommand",
    "AddReminderToDayHandler",
    "AddRoutineDefinitionToDayCommand",
    "AddRoutineDefinitionToDayHandler",
    "RemoveAlarmFromDayCommand",
    "RemoveAlarmFromDayHandler",
    "RemoveReminderCommand",
    "RemoveReminderHandler",
    "RescheduleDayCommand",
    "RescheduleDayHandler",
    "ScheduleDayCommand",
    "ScheduleDayHandler",
    "UpdateAlarmStatusCommand",
    "UpdateAlarmStatusHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
    "UpdateReminderStatusCommand",
    "UpdateReminderStatusHandler",
]
