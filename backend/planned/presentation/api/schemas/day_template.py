"""DayTemplate schema."""

from typing import TYPE_CHECKING, Optional

from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from .alarm import AlarmSchema


class DayTemplateSchema(BaseEntitySchema):
    """API schema for DayTemplate entity."""

    user_id: UUID
    slug: str
    alarm: Optional["AlarmSchema"] = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)


class DayTemplateUpdateSchema(BaseSchema):
    """API schema for DayTemplate update requests."""

    slug: str | None = None
    alarm: Optional["AlarmSchema"] = None
    icon: str | None = None
    routine_ids: list[UUID] | None = None

