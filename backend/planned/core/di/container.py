"""Dependency injection container implementation."""

from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")


class DIContainer:
    """Simple dependency injection container.
    
    Supports both singleton and factory patterns for dependency management.
    """

    def __init__(self) -> None:
        """Initialize the DI container."""
        self._singletons: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Callable[[], Any]] = {}

    def register_singleton(self, interface: type[T], implementation: T) -> None:
        """Register a singleton instance for an interface.
        
        Args:
            interface: The interface/protocol type
            implementation: The concrete instance to use
        """
        self._singletons[interface] = implementation

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for an interface.
        
        Args:
            interface: The interface/protocol type
            factory: A callable that returns an instance of the interface
        """
        self._factories[interface] = factory

    def get(self, interface: type[T]) -> T:
        """Get an instance of the interface.
        
        Args:
            interface: The interface/protocol type to resolve
            
        Returns:
            An instance of the interface
            
        Raises:
            KeyError: If the interface is not registered
        """
        # Check singletons first
        if interface in self._singletons:
            return cast(T, self._singletons[interface])
        
        # Check factories
        if interface in self._factories:
            instance = self._factories[interface]()
            return cast(T, instance)
        
        raise KeyError(f"Interface {interface} is not registered in the DI container")

    def get_or_none(self, interface: type[T]) -> T | None:
        """Get an instance of the interface, or None if not registered.
        
        Args:
            interface: The interface/protocol type to resolve
            
        Returns:
            An instance of the interface, or None if not registered
        """
        try:
            return self.get(interface)
        except KeyError:
            return None

