from collections.abc import Callable
from typing import Generic, TypeVar, cast, overload

T = TypeVar("T")  # The class/instance type
R = TypeVar("R")  # Return type (works with Coroutine for async methods)


class hybridmethod(Generic[T, R]):
    """Descriptor that allows different behavior for instance vs class calls."""

    def __init__(self, instance_method: Callable[[T], R]) -> None:
        self.instance_method = instance_method
        self.class_method: Callable[..., R] | None = None

    def classmethod(self, class_method: Callable[..., R]) -> "hybridmethod[T, R]":
        self.class_method = class_method
        return self

    @overload
    def __get__(self, obj: None, cls: type[T]) -> Callable[..., R]: ...

    @overload
    def __get__(self, obj: T, cls: type[T]) -> Callable[[], R]: ...

    def __get__(self, obj: T | None, cls: type[T]) -> Callable[..., R]:
        if obj is None:
            # Called on class (e.g., MyClass.load_context)
            if self.class_method is None:
                raise TypeError("No classmethod defined for this hybridmethod")
            return cast("Callable[..., R]", self.class_method.__get__(cls, type(cls)))
        # Called on instance (e.g., self.load_context)
        return cast("Callable[..., R]", self.instance_method.__get__(obj, cls))
