"""Entity signal registry for cross-layer event subscription.

This registry allows the infrastructure layer to register signals
and the application layer to subscribe to them without circular imports.

This solves the architectural issue where application services need to
listen to repository events but shouldn't import from infrastructure.

Usage:
    # In infrastructure (repositories automatically register on class creation):
    # No manual registration needed - handled by BaseRepository.__init_subclass__

    # In application layer:
    from planned.common.signal_registry import entity_signals, EntityType

    entity_signals.connect(EntityType.EVENT, self.on_event_change)
    entity_signals.connect(EntityType.TASK, self.on_task_change)
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from blinker import Signal

if TYPE_CHECKING:
    from planned.common.repository_handler import ChangeHandler


class EntityType(Enum):
    """Enumeration of all entity types that can emit repository events.

    Using an enum instead of strings provides:
    - Type safety: typos are caught at import time, not runtime
    - IDE support: autocomplete and jump-to-definition
    - Refactoring safety: renaming is caught by the type checker
    """

    # Core entities
    USER = auto()
    DAY = auto()
    DAY_TEMPLATE = auto()

    # Calendar & events
    CALENDAR = auto()
    EVENT = auto()

    # Tasks & routines
    TASK = auto()
    TASK_DEFINITION = auto()
    ROUTINE = auto()

    # Communication
    MESSAGE = auto()
    PUSH_SUBSCRIPTION = auto()

    # Auth
    AUTH_TOKEN = auto()


# Mapping from entity class names to EntityType enum values
# This allows repositories to register by class name and get the correct enum
_CLASS_NAME_TO_ENTITY_TYPE: dict[str, EntityType] = {
    "User": EntityType.USER,
    "Day": EntityType.DAY,
    "DayTemplate": EntityType.DAY_TEMPLATE,
    "Calendar": EntityType.CALENDAR,
    "Event": EntityType.EVENT,
    "Task": EntityType.TASK,
    "TaskDefinition": EntityType.TASK_DEFINITION,
    "Routine": EntityType.ROUTINE,
    "Message": EntityType.MESSAGE,
    "PushSubscription": EntityType.PUSH_SUBSCRIPTION,
    "AuthToken": EntityType.AUTH_TOKEN,
}


class EntitySignalRegistry:
    """Registry for entity-level signals with type-safe subscriptions.

    Infrastructure repositories register their signals here during class creation.
    Application services can subscribe via EntityType enum without importing infrastructure.

    This is a singleton - use the `entity_signals` instance.
    """

    _instance: "EntitySignalRegistry | None" = None
    _signals: dict[EntityType, Signal]

    def __new__(cls) -> "EntitySignalRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._signals = {}
        return cls._instance

    def register(self, entity_name: str, signal: Signal) -> None:
        """Register a signal for an entity type.

        Called automatically by BaseRepository.__init_subclass__ when
        repository classes are defined.

        Args:
            entity_name: The class name of the entity (e.g., "User", "Event", "Task")
            signal: The blinker Signal instance
        """
        entity_type = _CLASS_NAME_TO_ENTITY_TYPE.get(entity_name)
        if entity_type is not None:
            self._signals[entity_type] = signal

    def get_signal(self, entity_type: EntityType) -> Signal | None:
        """Get the signal for an entity type.

        Args:
            entity_type: The entity type enum value

        Returns:
            The Signal instance, or None if not registered
        """
        return self._signals.get(entity_type)

    def connect(self, entity_type: EntityType, handler: "ChangeHandler[Any]") -> bool:
        """Connect a handler to an entity's signal.

        Args:
            entity_type: The entity type to subscribe to (e.g., EntityType.TASK)
            handler: The handler to connect. Should accept (sender, *, event: RepositoryEvent)

        Returns:
            True if connected, False if entity not registered
        """
        signal = self._signals.get(entity_type)
        if signal is not None:
            signal.connect(handler)
            return True
        return False

    def disconnect(self, entity_type: EntityType, handler: "ChangeHandler[Any]") -> bool:
        """Disconnect a handler from an entity's signal.

        Args:
            entity_type: The entity type to unsubscribe from
            handler: The handler to disconnect

        Returns:
            True if disconnected, False if entity not registered
        """
        signal = self._signals.get(entity_type)
        if signal is not None:
            signal.disconnect(handler)
            return True
        return False

    def get_registered_entities(self) -> list[EntityType]:
        """Get a list of all registered entity types.

        Useful for debugging and introspection.

        Returns:
            List of EntityType values that have registered signals
        """
        return list(self._signals.keys())

    def is_registered(self, entity_type: EntityType) -> bool:
        """Check if an entity type has a registered signal.

        Args:
            entity_type: The entity type to check

        Returns:
            True if the entity type has a registered signal
        """
        return entity_type in self._signals


# Singleton instance - use this in application code
entity_signals = EntitySignalRegistry()
