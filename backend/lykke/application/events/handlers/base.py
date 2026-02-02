"""Base class for domain event handlers."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar
from uuid import UUID

from loguru import logger

# Import signal here to avoid circular imports
from lykke.application.base_handler import BaseHandler
from lykke.application.events.signals import domain_event_signal
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from lykke.domain.events.base import DomainEvent


class DomainEventHandler(ABC, BaseHandler):
    """Base class for domain event handlers with explicit dependency wiring.

    Subclasses declare which event types they handle via the `handles`
    class variable. Handlers are automatically registered and instantiated
    per user when events are dispatched.

    All concrete subclasses are automatically tracked and can be registered
    via `register_all_handlers()`. Repositories are exposed explicitly from the
    provided `ReadOnlyRepositories` instance.

    Example:
        class MyHandler(DomainEventHandler):
            handles = [TaskCompletedEvent]
            task_ro_repo: TaskRepositoryReadOnlyProtocol
            preview_day_handler: PreviewDayHandler

            async def handle(self, event: DomainEvent) -> None:
                # user_id is always available as self.user_id
                # Access repositories and handlers directly (same pattern as BaseCommandHandler)
                tasks = await self.task_ro_repo.search(...)
                preview = await self.preview_day_handler.preview_day(...)

        # At startup, all handlers are auto-registered:
        DomainEventHandler.register_all_handlers(
            ro_repo_factory=ro_repo_factory,
            uow_factory=uow_factory
        )
    """

    handles: ClassVar[list[type[DomainEvent]]] = []

    # Registry of all concrete handler classes
    _handler_classes: ClassVar[list[type["DomainEventHandler"]]] = []

    # Factory references for creating handler instances per user (class variables)
    _class_ro_repo_factory: ClassVar[ReadOnlyRepositoryFactory | None] = None
    _class_uow_factory: ClassVar[UnitOfWorkFactory | None] = None
    _class_handler_factory: ClassVar[
        Callable[
            [
                type["DomainEventHandler"],
                ReadOnlyRepositories,
                UUID,
                UnitOfWorkFactory | None,
            ],
            "DomainEventHandler",
        ]
        | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Track all concrete subclasses for auto-registration."""
        super().__init_subclass__(**kwargs)
        # Only register concrete classes (those with handles defined and not ABC)
        if cls.handles and not getattr(cls, "__abstractmethods__", None):
            DomainEventHandler._handler_classes.append(cls)

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        user_id: UUID,
        uow_factory: UnitOfWorkFactory | None = None,
    ) -> None:
        """Initialize the event handler with explicit dependencies."""
        super().__init__(ro_repos, user_id)
        self._uow_factory = uow_factory

    @classmethod
    def _extract_user_id(cls, event: DomainEvent) -> UUID | None:
        """Extract user_id from an event if available.

        Args:
            event: The domain event

        Returns:
            The user_id if available, None otherwise
        """
        # Try to get user_id from the event
        user_id = getattr(event, "user_id", None)
        if isinstance(user_id, UUID):
            return user_id
        # Try to get user_id from entity if event has an entity reference
        entity = getattr(event, "entity", None)
        if entity is not None:
            entity_user_id = getattr(entity, "user_id", None)
            if isinstance(entity_user_id, UUID):
                return entity_user_id
        return None

    @classmethod
    async def _dispatch_event(cls, *args: object, **kwargs: object) -> None:
        """Class-level dispatcher that creates user-scoped handler instances for events.

        This method is connected to the blinker signal and creates handler instances
        per user when events are dispatched.

        Args:
            args/kwargs: Arguments from the signal (expects `sender` and `event`)
        """
        sender = kwargs.pop("sender", args[0] if args else None)
        event_obj = kwargs.get("event")
        if not isinstance(event_obj, DomainEvent):
            logger.warning(
                f"Received signal without DomainEvent payload; sender={getattr(sender, '__name__', sender)} kwargs={kwargs}",
            )
            return

        # Extract user_id from event
        user_id = cls._extract_user_id(event_obj)
        if user_id is None:
            # Skip events without user_id
            return

        # Create handler instances for all handlers that handle this event type
        for handler_class in cls._handler_classes:
            if event_obj.__class__ in handler_class.handles:
                # Create a user-scoped instance of this handler
                if cls._class_ro_repo_factory is None:
                    logger.warning(
                        "No ReadOnlyRepositoryFactory set; "
                        f"cannot instantiate handler {handler_class.__name__}"
                    )
                    continue  # Skip if factories not set up

                ro_repos = cls._class_ro_repo_factory.create(user_id)
                if cls._class_handler_factory is not None:
                    handler_instance = cls._class_handler_factory(
                        handler_class,
                        ro_repos,
                        user_id,
                        cls._class_uow_factory,
                    )
                else:
                    handler_instance = handler_class(
                        ro_repos=ro_repos,
                        user_id=user_id,
                        uow_factory=cls._class_uow_factory,
                    )
                await handler_instance.handle(event_obj)

    @classmethod
    def register_all_handlers(
        cls,
        ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
        uow_factory: UnitOfWorkFactory | None = None,
        handler_factory: Callable[
            [
                type["DomainEventHandler"],
                ReadOnlyRepositories,
                UUID,
                UnitOfWorkFactory | None,
            ],
            "DomainEventHandler",
        ]
        | None = None,
    ) -> None:
        """Register all tracked handler classes and connect them to the event signal.

        This method stores the factories as class variables and connects a single
        dispatcher to the event signal. Handler instances are created per user
        when events are dispatched.

        Args:
            ro_repo_factory: Factory for creating read-only repositories.
                Required if any handler needs to inject repositories or handlers.
            uow_factory: Factory for creating UnitOfWork instances.
                Required if any handler needs to inject command handlers.
        """
        # Store factories as class variables for use when creating handler instances
        cls._class_ro_repo_factory = ro_repo_factory
        cls._class_uow_factory = uow_factory
        cls._class_handler_factory = handler_factory

        # Connect the dispatcher to all event types handled by any registered handler
        event_types: set[type[DomainEvent]] = set()
        for handler_class in cls._handler_classes:
            event_types.update(handler_class.handles)

        # To avoid sender mismatches (and duplicate connections on reload),
        # connect the dispatcher once without a sender filter and handle
        # filtering inside _dispatch_event.
        domain_event_signal.disconnect(cls._dispatch_event)
        domain_event_signal.disconnect(cls._dispatch_event, sender=None)
        domain_event_signal.connect(cls._dispatch_event, weak=False)

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
