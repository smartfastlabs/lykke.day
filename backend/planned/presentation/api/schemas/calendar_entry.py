"""CalendarEntry schema."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.task import TaskFrequency

from .action import ActionSchema
from .base import BaseEntitySchema
from .person import PersonSchema


class CalendarEntrySchema(BaseEntitySchema):
    """API schema for CalendarEntry entity."""

    user_id: UUID
    name: str
    calendar_id: UUID
    platform_id: str
    platform: str
    status: str
    starts_at: datetime
    frequency: TaskFrequency
    ends_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    people: list[PersonSchema] = Field(default_factory=list)
    actions: list[ActionSchema] = Field(default_factory=list)
    date: date  # Computed field from starts_at

