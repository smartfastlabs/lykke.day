"""Domain event infrastructure.

This module provides:
- Blinker signal for domain event dispatch
- Base class for creating event handlers
- Auto-registration of all event handlers
"""

from .handlers import DomainEventHandler, TaskStatusLoggerHandler
from .signals import domain_event_signal, send_domain_events
from planned.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)


def register_all_handlers(
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
) -> list[DomainEventHandler]:
    """Instantiate and register all domain event handlers.

    All subclasses of DomainEventHandler are automatically tracked
    and will be instantiated when this function is called.

    Args:
        ro_repo_factory: Optional factory for creating read-only repositories.
            Required if any handler needs to inject repositories or handlers.
        uow_factory: Optional factory for creating UnitOfWork instances.
            Required if any handler needs to inject command handlers.

    Returns:
        List of instantiated handler instances
    """
    return DomainEventHandler.register_all_handlers(
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


__all__ = [
    "DomainEventHandler",
    "TaskStatusLoggerHandler",
    "domain_event_signal",
    "register_all_handlers",
    "send_domain_events",
]
