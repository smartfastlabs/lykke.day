"""Domain event handlers.

Handlers are registered at application startup by instantiating them.
Each handler connects to the blinker signal for the event types it handles.
"""

from .base import DomainEventHandler
from .task_status_logger import TaskStatusLoggerHandler
from .user_forgot_password_logger import UserForgotPasswordLoggerHandler

__all__ = [
    "DomainEventHandler",
    "TaskStatusLoggerHandler",
    "UserForgotPasswordLoggerHandler",
]
