"""Query handler dependency injection functions organized by entity."""

from .calendar import (
    get_get_calendar_handler,
    get_list_calendars_handler,
)
from .calendar_entry_series import (
    get_get_calendar_entry_series_handler,
    get_list_calendar_entry_series_handler,
)
from .calendar_entry import get_list_calendar_entries_handler
from .day_template import (
    get_get_day_template_handler,
    get_list_day_templates_handler,
)
from .push_subscription import get_list_push_subscriptions_handler
from .routine import (
    get_get_routine_handler,
    get_list_routines_handler,
)
from .task import get_list_tasks_handler
from .task_definition import (
    get_get_task_definition_handler,
    get_list_task_definitions_handler,
)

__all__ = [
    # Calendar
    "get_get_calendar_handler",
    "get_list_calendars_handler",
    # TaskDefinition
    "get_get_task_definition_handler",
    "get_list_task_definitions_handler",
    # DayTemplate
    "get_get_day_template_handler",
    "get_list_day_templates_handler",
    # Routine
    "get_get_routine_handler",
    "get_list_routines_handler",
    # PushSubscription
    "get_list_push_subscriptions_handler",
    # CalendarEntry
    "get_list_calendar_entries_handler",
    # CalendarEntrySeries
    "get_get_calendar_entry_series_handler",
    "get_list_calendar_entry_series_handler",
    # Task
    "get_list_tasks_handler",
]

