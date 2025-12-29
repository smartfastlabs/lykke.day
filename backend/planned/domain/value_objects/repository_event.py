"""Repository change event value object.

Represents a change event for a repository object (create, update, or delete).
"""

from typing import Generic, Literal, TypeVar

import pydantic

ObjectType = TypeVar("ObjectType")


class RepositoryEvent(pydantic.BaseModel, Generic[ObjectType]):
    """Represents a change event for a repository object."""

    type: Literal["create", "update", "delete"]
    value: ObjectType

    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

