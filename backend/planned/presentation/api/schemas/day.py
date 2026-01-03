"""Day schema."""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.day import DayStatus, DayTag

from .alarm import AlarmSchema
from .base import BaseEntitySchema
from .day_template import DayTemplateSchema


class DaySchema(BaseEntitySchema):
    """API schema for Day entity."""

    user_id: UUID
    date: date
    alarm: AlarmSchema | None = None
    status: DayStatus
    scheduled_at: datetime | None = None
    tags: list[DayTag] = Field(default_factory=list)
    template: DayTemplateSchema | None = None

