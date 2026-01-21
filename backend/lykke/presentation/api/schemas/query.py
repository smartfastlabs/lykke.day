"""Query schema for paginated search requests."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Generic type for the query filters
QueryType = TypeVar("QueryType")


class QuerySchema(BaseModel, Generic[QueryType]):
    """Schema for query requests with pagination and filters."""

    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    filters: QueryType | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
