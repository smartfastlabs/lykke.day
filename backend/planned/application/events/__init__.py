"""Domain event infrastructure.

This module provides:
- Blinker signal for domain event dispatch
- Base class for creating event handlers
- Built-in event handlers
"""

from .handlers import DomainEventHandler, TaskStatusLoggerHandler
from .signals import domain_event_signal, send_domain_events

__all__ = [
    "domain_event_signal",
    "send_domain_events",
    "DomainEventHandler",
    "TaskStatusLoggerHandler",
]
