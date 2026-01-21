"""Domain event infrastructure.

This module provides:
- Blinker signal for domain event dispatch
- Base class for creating event handlers
- Auto-registration of all event handlers
"""

from .handlers import (
    DomainEventHandler,
    TaskStatusLoggerHandler,
    UserForgotPasswordLoggerHandler,
)
from .signals import domain_event_signal, send_domain_events
from lykke.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)


def register_all_handlers(
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
) -> None:
    """Register all domain event handler classes.

    All subclasses of DomainEventHandler are automatically tracked
    and will be registered when this function is called. Handler instances
    are created per user when events are dispatched.

    Args:
        ro_repo_factory: Factory for creating read-only repositories.
            Required if any handler needs to inject repositories or handlers.
        uow_factory: Factory for creating UnitOfWork instances.
            Required if any handler needs to inject command handlers.
    """
    DomainEventHandler.register_all_handlers(
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


__all__ = [
    "DomainEventHandler",
    "TaskStatusLoggerHandler",
    "UserForgotPasswordLoggerHandler",
    "domain_event_signal",
    "register_all_handlers",
    "send_domain_events",
]
