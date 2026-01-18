"""Day schema."""

from typing import TYPE_CHECKING, Optional

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects.day import DayStatus, DayTag

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from .brain_dump import BrainDumpItemSchema
    from .day_template import DayTemplateSchema
    from .goal import GoalSchema


class DaySchema(BaseEntitySchema):
    """API schema for Day entity."""

    user_id: UUID
    date: date
    status: DayStatus
    scheduled_at: datetime | None = None
    tags: list[DayTag] = Field(default_factory=list)
    template: Optional["DayTemplateSchema"] = None
    goals: list["GoalSchema"] = Field(default_factory=list)
    brain_dump_items: list["BrainDumpItemSchema"] = Field(default_factory=list)


class DayUpdateSchema(BaseSchema):
    """API schema for Day update requests."""

    status: DayStatus | None = None
    scheduled_at: datetime | None = None
    tags: list[DayTag] | None = None
    template_id: UUID | None = None

