"""Base class for domain event handlers."""

from abc import ABC, abstractmethod
from typing import ClassVar, Type

from planned.domain.events.base import DomainEvent

# Import signal here to avoid circular imports
from planned.application.events.signals import domain_event_signal


class DomainEventHandler(ABC):
    """Base class for domain event handlers.

    Subclasses declare which event types they handle via the `handles`
    class variable. When instantiated, the handler automatically connects
    to the blinker signal for those event types.

    Example:
        class MyHandler(DomainEventHandler):
            handles = [TaskCompletedEvent]

            async def handle(self, event: DomainEvent) -> None:
                # React to the event
                pass

        # At startup:
        handler = MyHandler()  # Automatically connected
    """

    handles: ClassVar[list[Type[DomainEvent]]] = []

    def __init__(self) -> None:
        """Connect this handler to the domain event signal."""
        for event_type in self.handles:
            domain_event_signal.connect(self._on_event, sender=event_type)

    async def _on_event(
        self,
        sender: Type[DomainEvent],
        event: DomainEvent,
    ) -> None:
        """Callback invoked by blinker when an event is dispatched."""
        await self.handle(event)

    def disconnect(self) -> None:
        """Disconnect from all event signals. Useful for testing."""
        for event_type in self.handles:
            domain_event_signal.disconnect(self._on_event, sender=event_type)

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle the domain event.

        Args:
            event: The domain event to handle
        """
        ...

