"""Query objects for building flexible queries with pagination, ordering, and filtering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

import pydantic

from .base import BaseRequestObject, BaseResponseObject


class BaseQuery(pydantic.BaseModel):
    """Base query class for building flexible queries with pagination, ordering, and filtering."""

    limit: int | None = None
    offset: int | None = None
    order_by: str | None = None
    order_by_desc: bool | None = None
    created_before: datetime | None = None
    created_after: datetime | None = None

    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class DateQuery(BaseQuery):
    """Query class for entities with a date column."""

    date: dt_date | None = None


class UserQuery(BaseQuery):
    """Query class for User entities."""

    email: str | None = None
    phone_number: str | None = None


class DayTemplateQuery(BaseQuery):
    """Query class for DayTemplate entities."""

    slug: str | None = None


class AuthTokenQuery(BaseQuery):
    """Query class for AuthToken entities."""

    user_id: UUID | None = None
    platform: str | None = None


class CalendarQuery(BaseQuery):
    """Query class for Calendar entities."""


class CalendarEntryQuery(DateQuery):
    """Query class for CalendarEntry entities."""


class DayQuery(DateQuery):
    """Query class for Day entities."""


class PushSubscriptionQuery(BaseQuery):
    """Query class for PushSubscription entities."""


class RoutineQuery(BaseQuery):
    """Query class for Routine entities."""


class TaskQuery(DateQuery):
    """Query class for Task entities."""


class TaskDefinitionQuery(BaseQuery):
    """Query class for TaskDefinition entities."""


T = TypeVar("T", bound=BaseQuery)


class PagedQueryRequest(BaseRequestObject, Generic[T]):
    """Request wrapper for paginated queries."""

    limit: int = pydantic.Field(default=50, ge=1, le=1000)
    offset: int = pydantic.Field(default=0, ge=0)
    query: T | None = None  # Optional nested query object (DateQuery, BaseQuery, etc.)


EntityType = TypeVar("EntityType")


@dataclass(kw_only=True)
class PagedQueryResponse(BaseResponseObject, Generic[EntityType]):
    """Response wrapper for paginated query results."""

    items: list[EntityType]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool
