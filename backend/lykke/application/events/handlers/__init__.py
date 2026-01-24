"""Domain event handlers.

Handlers are registered at application startup by instantiating them.
Each handler connects to the blinker signal for the event types it handles.
"""

from .base import DomainEventHandler
from .brain_dump_processing_trigger import BrainDumpProcessingTriggerHandler
from .calendar_entry_push_notifications import CalendarEntryPushNotificationHandler
from .smart_notification_trigger import SmartNotificationTriggerHandler
from .task_status_logger import TaskStatusLoggerHandler
from .user_forgot_password_logger import UserForgotPasswordLoggerHandler

__all__ = [
    "BrainDumpProcessingTriggerHandler",
    "CalendarEntryPushNotificationHandler",
    "DomainEventHandler",
    "SmartNotificationTriggerHandler",
    "TaskStatusLoggerHandler",
    "UserForgotPasswordLoggerHandler",
]
