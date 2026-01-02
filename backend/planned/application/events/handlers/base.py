"""Base class for domain event handlers."""

from abc import ABC, abstractmethod
from typing import ClassVar, Type

# Import signal here to avoid circular imports
from planned.application.events.signals import domain_event_signal
from planned.domain.events.base import DomainEvent


class DomainEventHandler(ABC):
    """Base class for domain event handlers.

    Subclasses declare which event types they handle via the `handles`
    class variable. When instantiated, the handler automatically connects
    to the blinker signal for those event types.

    All concrete subclasses are automatically tracked and can be instantiated
    via `register_all_handlers()`.

    Example:
        class MyHandler(DomainEventHandler):
            handles = [TaskCompletedEvent]

            async def handle(self, event: DomainEvent) -> None:
                # React to the event
                pass

        # At startup, all handlers are auto-registered:
        handlers = DomainEventHandler.register_all_handlers()
    """

    handles: ClassVar[list[type[DomainEvent]]] = []

    # Registry of all concrete handler classes
    _handler_classes: ClassVar[list[type["DomainEventHandler"]]] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Track all concrete subclasses for auto-registration."""
        super().__init_subclass__(**kwargs)
        # Only register concrete classes (those with handles defined and not ABC)
        if cls.handles and not getattr(cls, "__abstractmethods__", None):
            DomainEventHandler._handler_classes.append(cls)

    def __init__(self) -> None:
        """Connect this handler to the domain event signal."""
        for event_type in self.handles:
            domain_event_signal.connect(self._on_event, sender=event_type)

    async def _on_event(
        self,
        sender: type[DomainEvent],
        event: DomainEvent,
    ) -> None:
        """Callback invoked by blinker when an event is dispatched."""
        await self.handle(event)

    def disconnect(self) -> None:
        """Disconnect from all event signals. Useful for testing."""
        for event_type in self.handles:
            domain_event_signal.disconnect(self._on_event, sender=event_type)

    @classmethod
    def register_all_handlers(cls) -> list["DomainEventHandler"]:
        """Instantiate and register all tracked handler classes.

        Returns:
            List of instantiated handler instances
        """
        return [handler_cls() for handler_cls in cls._handler_classes]

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the handler registry. Useful for testing."""
        cls._handler_classes.clear()

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle the domain event.

        Args:
            event: The domain event to handle
        """
