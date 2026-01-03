"""Day schema."""

from typing import TYPE_CHECKING, Optional

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from planned.domain.value_objects.day import DayStatus, DayTag

from .base import BaseEntitySchema

if TYPE_CHECKING:
    from .alarm import AlarmSchema
    from .day_template import DayTemplateSchema


class DaySchema(BaseEntitySchema):
    """API schema for Day entity."""

    user_id: UUID
    date: date
    alarm: Optional["AlarmSchema"] = None
    status: DayStatus
    scheduled_at: datetime | None = None
    tags: list[DayTag] = Field(default_factory=list)
    template: Optional["DayTemplateSchema"] = None

