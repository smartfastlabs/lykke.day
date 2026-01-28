"""Day schema."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.day import DayStatus, DayTag

from .base import BaseEntitySchema, BaseSchema
from .high_level_plan import HighLevelPlanSchema

if TYPE_CHECKING:
    from .alarm import AlarmSchema
    from .brain_dump import BrainDumpSchema
    from .day_template import DayTemplateSchema
    from .reminder import ReminderSchema


class DaySchema(BaseEntitySchema):
    """API schema for Day entity."""

    user_id: UUID
    date: date
    status: DayStatus
    scheduled_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    tags: list[DayTag] = Field(default_factory=list)
    template: Optional["DayTemplateSchema"] = None
    reminders: list["ReminderSchema"] = Field(default_factory=list)
    alarms: list["AlarmSchema"] = Field(default_factory=list)
    brain_dump_items: list["BrainDumpSchema"] = Field(default_factory=list)
    high_level_plan: HighLevelPlanSchema | None = None


class DayUpdateSchema(BaseSchema):
    """API schema for Day update requests."""

    status: DayStatus | None = None
    scheduled_at: datetime | None = None
    tags: list[DayTag] | None = None
    template_id: UUID | None = None
    alarms: list["AlarmSchema"] | None = None
    high_level_plan: HighLevelPlanSchema | None = None
