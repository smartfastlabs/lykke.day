"""Entity signal registry for cross-layer event subscription.

This registry allows the infrastructure layer to register signals
and the application layer to subscribe to them without circular imports.

This solves the architectural issue where application services need to
listen to repository events but shouldn't import from infrastructure.

Usage:
    # In infrastructure (repositories automatically register on class creation):
    # No manual registration needed - handled by BaseRepository.__init_subclass__

    # In application layer:
    from planned.common.signal_registry import entity_signals

    entity_signals.connect("Event", self.on_event_change)
    entity_signals.connect("Task", self.on_task_change)
"""

from typing import TYPE_CHECKING, Any

from blinker import Signal

if TYPE_CHECKING:
    from planned.common.repository_handler import ChangeHandler


class EntitySignalRegistry:
    """Registry for entity-level signals.

    Infrastructure repositories register their signals here during class creation.
    Application services can subscribe via entity name without importing infrastructure.

    This is a singleton - use the `entity_signals` instance.
    """

    _instance: "EntitySignalRegistry | None" = None
    _signals: dict[str, Signal]

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
            entity_name: The name of the entity (e.g., "User", "Event", "Task")
            signal: The blinker Signal instance
        """
        self._signals[entity_name] = signal

    def get_signal(self, entity_name: str) -> Signal | None:
        """Get the signal for an entity type.

        Args:
            entity_name: The name of the entity

        Returns:
            The Signal instance, or None if not registered
        """
        return self._signals.get(entity_name)

    def connect(self, entity_name: str, handler: "ChangeHandler[Any]") -> bool:
        """Connect a handler to an entity's signal.

        Args:
            entity_name: The name of the entity (e.g., "User", "Event", "Task")
            handler: The handler to connect. Should accept (sender, *, event: RepositoryEvent)

        Returns:
            True if connected, False if entity not registered
        """
        signal = self._signals.get(entity_name)
        if signal is not None:
            signal.connect(handler)
            return True
        return False

    def disconnect(self, entity_name: str, handler: "ChangeHandler[Any]") -> bool:
        """Disconnect a handler from an entity's signal.

        Args:
            entity_name: The name of the entity
            handler: The handler to disconnect

        Returns:
            True if disconnected, False if entity not registered
        """
        signal = self._signals.get(entity_name)
        if signal is not None:
            signal.disconnect(handler)
            return True
        return False

    def get_registered_entities(self) -> list[str]:
        """Get a list of all registered entity names.

        Useful for debugging and introspection.

        Returns:
            List of entity names that have registered signals
        """
        return list(self._signals.keys())

    def is_registered(self, entity_name: str) -> bool:
        """Check if an entity has a registered signal.

        Args:
            entity_name: The name of the entity

        Returns:
            True if the entity has a registered signal
        """
        return entity_name in self._signals


# Singleton instance - use this in application code
entity_signals = EntitySignalRegistry()

