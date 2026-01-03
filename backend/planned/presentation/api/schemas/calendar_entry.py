"""CalendarEntry schema."""

from typing import TYPE_CHECKING

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.task import TaskFrequency

from .base import BaseEntitySchema

if TYPE_CHECKING:
    from .action import Action
    from .person import Person


class CalendarEntry(BaseEntitySchema):
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
    people: list["Person"] = Field(default_factory=list)
    actions: list["Action"] = Field(default_factory=list)
    date: date  # Computed field from starts_at

