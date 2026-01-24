"""Schemas for calendar entry series."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.task import EventCategory, TaskFrequency

from .base import BaseEntitySchema, BaseSchema


class CalendarEntrySeriesSchema(BaseEntitySchema):
    """API schema for CalendarEntrySeries entity."""

    user_id: UUID
    calendar_id: UUID
    name: str
    platform_id: str
    platform: str
    frequency: TaskFrequency
    event_category: EventCategory | None = None
    recurrence: list[str] = Field(default_factory=list)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CalendarEntrySeriesUpdateSchema(BaseSchema):
    """API schema for updating a CalendarEntrySeries."""

    name: str | None = None
    event_category: EventCategory | None = None
