"""Command handlers for state-changing operations.

Command handlers execute operations that change state, persist changes, and return results.
"""

from .bulk_create_entities import BulkCreateEntitiesHandler
from .create_entity import CreateEntityHandler
from .create_or_get_day import CreateOrGetDayHandler
from .delete_entity import DeleteEntityHandler
from .record_task_action import RecordTaskActionHandler
from .save_day import SaveDayHandler
from .schedule_day import ScheduleDayHandler
from .sync_calendar import SyncAllCalendarsHandler, SyncCalendarHandler
from .unschedule_day import UnscheduleDayHandler
from .update_day import UpdateDayHandler
from .update_entity import UpdateEntityHandler

__all__ = [
    "BulkCreateEntitiesHandler",
    "CreateEntityHandler",
    "CreateOrGetDayHandler",
    "DeleteEntityHandler",
    "RecordTaskActionHandler",
    "SaveDayHandler",
    "ScheduleDayHandler",
    "SyncAllCalendarsHandler",
    "SyncCalendarHandler",
    "UnscheduleDayHandler",
    "UpdateDayHandler",
    "UpdateEntityHandler",
]
