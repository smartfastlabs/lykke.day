"""Command handlers for state-changing operations.

Commands are immutable request objects that describe an intent to change state.
Command handlers execute the command, persist changes, and return results.
"""

from .base import Command, CommandHandler
from .bulk_create_entities import BulkCreateEntitiesCommand, BulkCreateEntitiesHandler
from .create_entity import CreateEntityCommand, CreateEntityHandler
from .delete_entity import DeleteEntityCommand, DeleteEntityHandler
from .record_task_action import RecordTaskActionCommand, RecordTaskActionHandler
from .schedule_day import ScheduleDayCommand, ScheduleDayHandler
from .update_day import UpdateDayCommand, UpdateDayHandler
from .update_entity import UpdateEntityCommand, UpdateEntityHandler

__all__ = [
    "BulkCreateEntitiesCommand",
    "BulkCreateEntitiesHandler",
    "Command",
    "CommandHandler",
    "CreateEntityCommand",
    "CreateEntityHandler",
    "DeleteEntityCommand",
    "DeleteEntityHandler",
    "RecordTaskActionCommand",
    "RecordTaskActionHandler",
    "ScheduleDayCommand",
    "ScheduleDayHandler",
    "UpdateDayCommand",
    "UpdateDayHandler",
    "UpdateEntityCommand",
    "UpdateEntityHandler",
]
