"""Pagination schema for API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

# Generic type for the items in the paginated response
ItemType = TypeVar("ItemType")


class PagedResponseSchema(BaseModel, Generic[ItemType]):
    """Schema for paginated API responses."""

    items: list[ItemType]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
