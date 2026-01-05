"""Base class for domain event handlers."""

import inspect
from abc import ABC, abstractmethod
from typing import Any, ClassVar, get_type_hints
from uuid import UUID

# Import signal here to avoid circular imports
from planned.application.events.signals import domain_event_signal
from planned.application.queries.base import BaseQueryHandler
from planned.application.unit_of_work import (
    ReadOnlyRepositories,
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from planned.domain.events.base import DomainEvent


class UserContextManager:
    """Context manager for setting user_id in event handlers."""

    def __init__(self, handler: "DomainEventHandler", user_id: UUID) -> None:
        """Initialize the context manager.

        Args:
            handler: The event handler instance
            user_id: The user ID to set
        """
        self.handler = handler
        self.user_id = user_id
        self.old_user_id: UUID | None = None

    def __enter__(self) -> "UserContextManager":
        """Enter the context and set user_id."""
        self.old_user_id = self.handler._current_user_id
        self.handler._current_user_id = self.user_id
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the context and restore previous user_id."""
        self.handler._current_user_id = self.old_user_id


class DomainEventHandler(ABC):
    """Base class for domain event handlers that automatically injects requested repositories and handlers.

    Subclasses declare which event types they handle via the `handles`
    class variable. When instantiated, the handler automatically connects
    to the blinker signal for those event types.

    Subclasses can also declare which repositories and handlers they need as class attributes
    with type annotations. These will be made available as instance attributes, created
    lazily per user_id when handling events.

    All concrete subclasses are automatically tracked and can be instantiated
    via `register_all_handlers()`.

    Example:
        class MyHandler(DomainEventHandler):
            handles = [TaskCompletedEvent]
            task_ro_repo: TaskRepositoryReadOnlyProtocol
            preview_day_handler: PreviewDayHandler

            async def handle(self, event: DomainEvent) -> None:
                # user_id is automatically extracted from event if available
                # Access repositories and handlers directly (same pattern as BaseCommandHandler)
                tasks = await self.task_ro_repo.search(...)
                preview = await self.preview_day_handler.preview_day(...)

                # Or manually set user_id if not in event:
                # async with self._with_user_id(user_id):
                #     tasks = await self.task_ro_repo.search(...)

        # At startup, all handlers are auto-registered:
        handlers = DomainEventHandler.register_all_handlers(
            ro_repo_factory=ro_repo_factory,
            uow_factory=uow_factory
        )
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

    def __init__(
        self,
        ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
        uow_factory: UnitOfWorkFactory | None = None,
    ) -> None:
        """Initialize the event handler with factories for creating repositories and handlers.

        Args:
            ro_repo_factory: Optional factory for creating read-only repositories.
                Required if the handler needs to inject repositories or handlers.
            uow_factory: Optional factory for creating UnitOfWork instances.
                Required if the handler needs to inject command handlers.
        """
        self._ro_repo_factory = ro_repo_factory
        self._uow_factory = uow_factory

        # Current user_id context (set when handling an event)
        self._current_user_id: UUID | None = None

        # Cache for repositories and handlers per user_id
        self._repo_cache: dict[UUID, ReadOnlyRepositories] = {}
        self._handler_cache: dict[tuple[str, UUID], Any] = {}

        # Get type hints from the class (including from base classes)
        annotations = get_type_hints(self.__class__, include_extras=True)

        # Store declared repository and handler attribute names and types
        self._declared_repos: dict[str, type] = {}
        self._declared_handlers: dict[str, type] = {}

        for attr_name, attr_type in annotations.items():
            # Skip private attributes and methods
            if attr_name.startswith("_") or attr_name in ("handles",):
                continue

            # Check if this is a repository attribute
            if self._is_repository_type(attr_type):
                self._declared_repos[attr_name] = attr_type
            # Check if this is a handler type
            elif self._is_handler_type(attr_type):
                self._declared_handlers[attr_name] = attr_type

        # Connect this handler to the domain event signal
        for event_type in self.handles:
            domain_event_signal.connect(self._on_event, sender=event_type)

    def __getattr__(self, name: str) -> Any:
        """Lazily create and return repositories or handlers when accessed.

        Args:
            name: The attribute name

        Returns:
            The repository or handler instance

        Raises:
            AttributeError: If the attribute is not declared or user_id is not set
        """
        if name in self._declared_repos:
            if self._current_user_id is None:
                raise AttributeError(
                    f"Cannot access {name} - user_id not set. "
                    f"Extract user_id from the event and use _with_user_id() context manager."
                )
            return self._get_repo_for_user(name, self._current_user_id)
        elif name in self._declared_handlers:
            if self._current_user_id is None:
                raise AttributeError(
                    f"Cannot access {name} - user_id not set. "
                    f"Extract user_id from the event and use _with_user_id() context manager."
                )
            return self._get_handler_for_user(name, self._current_user_id)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def _is_repository_type(self, attr_type: type) -> bool:
        """Check if a type is a repository protocol.

        Args:
            attr_type: The type to check

        Returns:
            True if the type is a repository protocol, False otherwise
        """
        # Check if it's a Protocol with a name ending in "Protocol"
        return (
            inspect.isclass(attr_type)
            and hasattr(attr_type, "__protocol_attrs__")
            and ("Repository" in attr_type.__name__ or "Protocol" in attr_type.__name__)
        )

    def _is_handler_type(self, attr_type: type) -> bool:
        """Check if a type is a handler (BaseCommandHandler or BaseQueryHandler subclass).

        Args:
            attr_type: The type to check

        Returns:
            True if the type is a handler, False otherwise
        """
        if not inspect.isclass(attr_type):
            return False

        # Check if it's a subclass of BaseCommandHandler or BaseQueryHandler
        mro = inspect.getmro(attr_type)
        # Import here to avoid circular imports
        from planned.application.commands.base import BaseCommandHandler

        return BaseCommandHandler in mro or BaseQueryHandler in mro

    def _get_repo_for_user(self, attr_name: str, user_id: UUID) -> Any:
        """Get a specific repository for a user.

        Args:
            attr_name: The repository attribute name
            user_id: The user ID

        Returns:
            The repository instance
        """
        if user_id not in self._repo_cache:
            if self._ro_repo_factory is None:
                raise ValueError(
                    f"ro_repo_factory is required to access repositories "
                    f"(requested: {attr_name})"
                )
            self._repo_cache[user_id] = self._ro_repo_factory.create(user_id)

        repos = self._repo_cache[user_id]
        # Return the specific repository attribute
        if hasattr(repos, attr_name):
            return getattr(repos, attr_name)
        raise AttributeError(
            f"Repository {attr_name} not found in ReadOnlyRepositories"
        )

    def _get_handler_for_user(self, attr_name: str, user_id: UUID) -> Any:
        """Get a handler instance for a specific user.

        Args:
            attr_name: The handler attribute name
            user_id: The user ID

        Returns:
            Handler instance for the user
        """
        cache_key = (attr_name, user_id)
        if cache_key in self._handler_cache:
            return self._handler_cache[cache_key]

        if attr_name not in self._declared_handlers:
            raise ValueError(
                f"Handler {attr_name} not declared in {self.__class__.__name__}"
            )

        handler_class = self._declared_handlers[attr_name]
        handler_instance = self._create_handler(handler_class, attr_name, user_id)
        self._handler_cache[cache_key] = handler_instance
        return handler_instance

    def _create_handler(
        self, handler_class: type, attr_name: str, user_id: UUID
    ) -> Any:
        """Create an instance of a handler for a specific user.

        Args:
            handler_class: The handler class to instantiate
            attr_name: The attribute name (for error messages)
            user_id: The user ID

        Returns:
            An instance of the handler

        Raises:
            ValueError: If required factories are not provided
        """
        # Import here to avoid circular imports
        from planned.application.commands.base import BaseCommandHandler

        mro = inspect.getmro(handler_class)
        if BaseCommandHandler in mro:
            # Command handlers need: ro_repos, uow_factory, user_id, ro_repo_factory
            if self._ro_repo_factory is None or self._uow_factory is None:
                raise ValueError(
                    f"ro_repo_factory and uow_factory are required to inject {attr_name} "
                    f"({handler_class.__name__})"
                )
            ro_repos = self._ro_repo_factory.create(user_id)
            return handler_class(
                ro_repos,
                self._uow_factory,
                user_id,
                self._ro_repo_factory,
            )
        elif issubclass(handler_class, BaseQueryHandler):
            # Query handlers need: ro_repos, user_id
            if self._ro_repo_factory is None:
                raise ValueError(
                    f"ro_repo_factory is required to inject {attr_name} "
                    f"({handler_class.__name__})"
                )
            ro_repos = self._ro_repo_factory.create(user_id)
            return handler_class(ro_repos, user_id)
        else:
            raise ValueError(f"Unknown handler type: {handler_class}")

    def _extract_user_id(self, event: DomainEvent) -> UUID | None:
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

    def _with_user_id(self, user_id: UUID) -> "UserContextManager":
        """Context manager to set user_id for accessing repositories and handlers.

        Args:
            user_id: The user ID to use

        Returns:
            A context manager that sets the user_id
        """
        return UserContextManager(self, user_id)

    async def _on_event(
        self,
        _sender: type[DomainEvent],
        event: DomainEvent,
    ) -> None:
        """Callback invoked by blinker when an event is dispatched."""
        # Try to extract user_id from event and set it in context
        user_id = self._extract_user_id(event)
        if user_id:
            old_user_id = self._current_user_id
            self._current_user_id = user_id
            try:
                await self.handle(event)
            finally:
                self._current_user_id = old_user_id
        else:
            # If no user_id in event, handle without context
            await self.handle(event)

    def disconnect(self) -> None:
        """Disconnect from all event signals. Useful for testing."""
        for event_type in self.handles:
            domain_event_signal.disconnect(self._on_event, sender=event_type)

    @classmethod
    def register_all_handlers(
        cls,
        ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
        uow_factory: UnitOfWorkFactory | None = None,
    ) -> list["DomainEventHandler"]:
        """Instantiate and register all tracked handler classes.

        Args:
            ro_repo_factory: Optional factory for creating read-only repositories.
                Required if any handler needs to inject repositories or handlers.
            uow_factory: Optional factory for creating UnitOfWork instances.
                Required if any handler needs to inject command handlers.

        Returns:
            List of instantiated handler instances
        """
        return [
            handler_cls(ro_repo_factory=ro_repo_factory, uow_factory=uow_factory)
            for handler_cls in cls._handler_classes
        ]

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
