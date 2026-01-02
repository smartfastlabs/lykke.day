"""Domain event infrastructure.

This module provides:
- Blinker signal for domain event dispatch
- Base class for creating event handlers
- Auto-registration of all event handlers
"""

from .handlers import DomainEventHandler, TaskStatusLoggerHandler
from .signals import domain_event_signal, send_domain_events


def register_all_handlers() -> list[DomainEventHandler]:
    """Instantiate and register all domain event handlers.

    All subclasses of DomainEventHandler are automatically tracked
    and will be instantiated when this function is called.

    Returns:
        List of instantiated handler instances
    """
    return DomainEventHandler.register_all_handlers()


__all__ = [
    "DomainEventHandler",
    "TaskStatusLoggerHandler",
    "domain_event_signal",
    "register_all_handlers",
    "send_domain_events",
]
