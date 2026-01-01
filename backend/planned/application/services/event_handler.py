"""Base event handler infrastructure for services."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from planned.application.events import domain_event_signal
from planned.domain.events.base import DomainEvent

# Type variable for the service that owns the event handler
ServiceT = TypeVar("ServiceT")


class EventHandler(ABC, Generic[ServiceT]):
    """Base class for domain event handlers.

    Event handlers subscribe to domain events and process them.
    Each handler is responsible for a specific category of events.

    Type Parameters:
        ServiceT: The type of service that owns this handler
    """

    _service: ServiceT | None

    def __init__(self) -> None:
        """Initialize the event handler."""
        self._service = None

    @property
    def service(self) -> ServiceT:
        """Get the parent service.

        Returns:
            The service that owns this handler

        Raises:
            RuntimeError: If the handler hasn't been registered with a service
        """
        if self._service is None:
            raise RuntimeError(
                f"{self.__class__.__name__} has not been registered with a service"
            )
        return self._service

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event.

        Args:
            event: The domain event to handle
        """
        ...

    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can handle the given event.

        Args:
            event: The domain event to check

        Returns:
            True if this handler can handle the event
        """
        ...


class EventHandlerMixin:
    """Mixin that provides event subscription functionality.

    Add this mixin to a service class and register event handlers
    to automatically dispatch domain events to the appropriate handlers.
    """

    _event_handlers: list[EventHandler[Any]]
    _is_subscribed: bool

    def _init_event_handlers(self) -> None:
        """Initialize the event handler list. Call this in __init__."""
        self._event_handlers = []
        self._is_subscribed = False

    def _register_handler(self, handler: EventHandler[Any]) -> None:
        """Register an event handler.

        Sets the handler's service reference to this service instance.

        Args:
            handler: The event handler to register
        """
        handler._service = self
        self._event_handlers.append(handler)

    def subscribe_to_events(self) -> None:
        """Subscribe to domain events."""
        if self._is_subscribed:
            return
        domain_event_signal.connect(self._dispatch_event)
        self._is_subscribed = True

    def unsubscribe_from_events(self) -> None:
        """Unsubscribe from domain events."""
        if not self._is_subscribed:
            return
        domain_event_signal.disconnect(self._dispatch_event)
        self._is_subscribed = False

    async def _dispatch_event(
        self,
        sender: type[DomainEvent],
        event: DomainEvent,
    ) -> None:
        """Dispatch an event to the appropriate handler(s).

        Args:
            sender: The event class (used by blinker for filtering)
            event: The domain event to dispatch
        """
        for handler in self._event_handlers:
            if handler.can_handle(event):
                await handler.handle(event)
