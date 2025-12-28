from typing import Any, Generic, TypeVar

from blinker import Signal

from planned.application.repositories.base import ChangeEvent, ChangeHandler

ObjectType = TypeVar("ObjectType")


class BaseRepository(Generic[ObjectType]):
    signal_source: Signal

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize a class-level signal for each repository subclass.
        This ensures all instances of the same repository class share the same signal.
        """
        super().__init_subclass__(**kwargs)
        cls.signal_source = Signal()

    def listen(self, handler: ChangeHandler[ObjectType]) -> None:
        """
        Connect a handler to receive ChangeEvent[ObjectType] notifications.

        The handler should accept (sender, *, event: ChangeEvent[ObjectType]) as parameters.
        """
        type(self).signal_source.connect(handler)
