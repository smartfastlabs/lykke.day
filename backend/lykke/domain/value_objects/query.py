"""Query objects for building flexible queries with pagination, ordering, and filtering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from .base import BaseRequestObject, BaseResponseObject, BaseValueObject



@dataclass(kw_only=True)
class BaseQuery(BaseValueObject):
    """Base query class for building flexible queries with pagination, ordering, and filtering."""

    limit: int | None = None
    offset: int | None = None
    order_by: str | None = None
    order_by_desc: bool | None = None
    created_before: datetime | None = None
    created_after: datetime | None = None


@dataclass(kw_only=True)
class DateQuery(BaseQuery):
    """Query class for entities with a date column."""

    date: dt_date | None = None


@dataclass(kw_only=True)
class UserQuery(BaseQuery):
    """Query class for User entities."""

    email: str | None = None
    phone_number: str | None = None


@dataclass(kw_only=True)
class DayTemplateQuery(BaseQuery):
    """Query class for DayTemplate entities."""

    slug: str | None = None


@dataclass(kw_only=True)
class AuthTokenQuery(BaseQuery):
    """Query class for AuthToken entities."""

    user_id: UUID | None = None
    platform: str | None = None


@dataclass(kw_only=True)
class CalendarQuery(BaseQuery):
    """Query class for Calendar entities."""

    subscription_id: str | None = None
    resource_id: str | None = None


@dataclass(kw_only=True)
class CalendarEntryQuery(DateQuery):
    """Query class for CalendarEntry entities."""

    calendar_id: UUID | None = None
    platform_id: str | None = None
    platform_ids: list[str] | None = None


@dataclass(kw_only=True)
class CalendarEntrySeriesQuery(BaseQuery):
    """Query class for CalendarEntrySeries entities."""

    calendar_id: UUID | None = None
    platform_id: str | None = None


@dataclass(kw_only=True)
class DayQuery(DateQuery):
    """Query class for Day entities."""


@dataclass(kw_only=True)
class PushSubscriptionQuery(BaseQuery):
    """Query class for PushSubscription entities."""


@dataclass(kw_only=True)
class RoutineQuery(BaseQuery):
    """Query class for Routine entities."""


@dataclass(kw_only=True)
class TaskQuery(DateQuery):
    """Query class for Task entities."""

    ids: list[UUID] | None = None
    routine_ids: list[UUID] | None = None


@dataclass(kw_only=True)
class TaskDefinitionQuery(BaseQuery):
    """Query class for TaskDefinition entities."""


@dataclass(kw_only=True)
class TimeBlockDefinitionQuery(BaseQuery):
    """Query class for TimeBlockDefinition entities."""


@dataclass(kw_only=True)
class ConversationQuery(BaseQuery):
    """Query class for Conversation entities."""

    channel: str | None = None
    status: str | None = None
    bot_personality_id: UUID | None = None


@dataclass(kw_only=True)
class MessageQuery(BaseQuery):
    """Query class for Message entities."""

    conversation_id: UUID | None = None
    role: str | None = None


@dataclass(kw_only=True)
class BotPersonalityQuery(BaseQuery):
    """Query class for BotPersonality entities."""

    name: str | None = None
    base_bot_personality_id: UUID | None = None


@dataclass(kw_only=True)
class FactoidQuery(BaseQuery):
    """Query class for Factoid entities."""

    conversation_id: UUID | None = None
    factoid_type: str | None = None
    criticality: str | None = None
    is_global: bool | None = None  # Filter for global vs conversation-specific factoids


@dataclass(kw_only=True)
class AuditLogQuery(BaseQuery):
    """Query class for AuditLog entities."""

    activity_type: str | None = None
    entity_id: UUID | None = None
    entity_type: str | None = None
    occurred_after: datetime | None = None
    occurred_before: datetime | None = None
    date: dt_date | None = None


T = TypeVar("T", bound=BaseQuery)


@dataclass(kw_only=True)
class PagedQueryRequest(BaseRequestObject, Generic[T]):
    """Request wrapper for paginated queries."""

    limit: int = 50
    offset: int = 0
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
