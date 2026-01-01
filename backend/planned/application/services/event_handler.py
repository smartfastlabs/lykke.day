"""Base event handler infrastructure for services."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from planned.application.events import domain_event_signal
from planned.domain.events.base import DomainEvent

# Type variable for the context that event handlers operate on
ContextT = TypeVar("ContextT")

# Type variable for the service that owns the event handler
ServiceT = TypeVar("ServiceT")


class EventHandler(ABC, Generic[ContextT, ServiceT]):
    """Base class for domain event handlers.

    Event handlers subscribe to domain events and update a shared context.
    Each handler is responsible for a specific category of events.

    Type Parameters:
        ContextT: The type of context this handler operates on
        ServiceT: The type of service that owns this handler
    """

    _service: ServiceT | None

    def __init__(self, ctx: ContextT) -> None:
        """Initialize the event handler.

        Args:
            ctx: The shared context to update when events occur
        """
        self._ctx = ctx
        self._service = None

    @property
    def ctx(self) -> ContextT:
        """Get the current context."""
        return self._ctx

    @ctx.setter
    def ctx(self, value: ContextT) -> None:
        """Update the context reference."""
        self._ctx = value

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


class EventHandlerMixin(Generic[ContextT]):
    """Mixin that provides event subscription functionality.

    Add this mixin to a service class and register event handlers
    to automatically dispatch domain events to the appropriate handlers.
    """

    _event_handlers: list[EventHandler[ContextT, Any]]
    _is_subscribed: bool

    def _init_event_handlers(self) -> None:
        """Initialize the event handler list. Call this in __init__."""
        self._event_handlers = []
        self._is_subscribed = False

    def _register_handler(self, handler: EventHandler[ContextT, Any]) -> None:
        """Register an event handler.

        Sets the handler's service reference to this service instance.

        Args:
            handler: The event handler to register
        """
        handler._service = self
        self._event_handlers.append(handler)

    def _update_handler_contexts(self, ctx: ContextT) -> None:
        """Update the context reference in all handlers.

        Args:
            ctx: The new context to set
        """
        for handler in self._event_handlers:
            handler.ctx = ctx

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
