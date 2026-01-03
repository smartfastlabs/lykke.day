"""DayTemplate schema."""

from typing import TYPE_CHECKING, Optional

from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema

if TYPE_CHECKING:
    from .alarm import AlarmSchema


class DayTemplateSchema(BaseEntitySchema):
    """API schema for DayTemplate entity."""

    user_id: UUID
    slug: str
    alarm: Optional["AlarmSchema"] = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)

