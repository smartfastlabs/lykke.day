"""CalendarEntry schema."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.task import (
    CalendarEntryAttendanceStatus,
    EventCategory,
    TaskFrequency,
)

from .base import BaseEntitySchema

if TYPE_CHECKING:
    from .action import ActionSchema


class CalendarEntrySchema(BaseEntitySchema):
    """API schema for CalendarEntry entity."""

    user_id: UUID
    name: str
    calendar_id: UUID
    platform_id: str
    platform: str
    status: str
    attendance_status: CalendarEntryAttendanceStatus | None = None
    starts_at: datetime
    frequency: TaskFrequency
    category: EventCategory | None = None
    ends_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    actions: list["ActionSchema"] = Field(default_factory=list)
    date: date  # Computed field from starts_at


class CalendarEntryUpdateSchema(BaseEntitySchema):
    """API schema for updating a CalendarEntry entity."""

    name: str | None = None
    status: str | None = None
    attendance_status: CalendarEntryAttendanceStatus | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    frequency: TaskFrequency | None = None
    category: EventCategory | None = None
    calendar_entry_series_id: UUID | None = None
