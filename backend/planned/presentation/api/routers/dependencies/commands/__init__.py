"""Command handler dependency injection functions organized by entity."""

from .calendar import (
    get_create_calendar_handler,
    get_delete_calendar_handler,
    get_update_calendar_handler,
)
from .day_template import (
    get_create_day_template_handler,
    get_delete_day_template_handler,
    get_update_day_template_handler,
)
from .push_subscription import (
    get_create_push_subscription_handler,
    get_delete_push_subscription_handler,
)
from .routine import (
    get_create_routine_handler,
    get_delete_routine_handler,
    get_update_routine_handler,
)
from .task_definition import (
    get_bulk_create_task_definitions_handler,
    get_create_task_definition_handler,
    get_delete_task_definition_handler,
    get_update_task_definition_handler,
)
from .user import get_update_user_handler

__all__ = [
    # Calendar
    "get_create_calendar_handler",
    "get_update_calendar_handler",
    "get_delete_calendar_handler",
    # TaskDefinition
    "get_create_task_definition_handler",
    "get_update_task_definition_handler",
    "get_delete_task_definition_handler",
    "get_bulk_create_task_definitions_handler",
    # DayTemplate
    "get_create_day_template_handler",
    "get_update_day_template_handler",
    "get_delete_day_template_handler",
    # PushSubscription
    "get_create_push_subscription_handler",
    "get_delete_push_subscription_handler",
    # Routine
    "get_create_routine_handler",
    "get_update_routine_handler",
    "get_delete_routine_handler",
    # User
    "get_update_user_handler",
]

