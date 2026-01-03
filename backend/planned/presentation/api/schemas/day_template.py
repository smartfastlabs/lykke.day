"""DayTemplate schema."""

from uuid import UUID

from pydantic import Field

from .alarm import AlarmSchema
from .base import BaseEntitySchema


class DayTemplateSchema(BaseEntitySchema):
    """API schema for DayTemplate entity."""

    user_id: UUID
    slug: str
    alarm: AlarmSchema | None = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)

