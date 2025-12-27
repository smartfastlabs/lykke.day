from typing import Any, Generic, Literal, Protocol, TypeVar

import pydantic
from blinker import Signal

ObjectType = TypeVar("ObjectType")


class ChangeEvent(pydantic.BaseModel, Generic[ObjectType]):
    type: Literal["create", "update", "delete"]
    value: ObjectType

    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ChangeHandler(Protocol[ObjectType]):
    async def __call__(
        self, _sender: object | None = None, *, event: ChangeEvent[ObjectType]
    ) -> None: ...


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
