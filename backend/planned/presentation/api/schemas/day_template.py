"""DayTemplate schema."""

from typing import TYPE_CHECKING, Optional

from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from .alarm import AlarmSchema


class DayTemplateCreateSchema(BaseSchema):
    """API schema for creating a DayTemplate entity."""

    slug: str
    alarm: Optional["AlarmSchema"] = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)


class DayTemplateSchema(DayTemplateCreateSchema, BaseEntitySchema):
    """API schema for DayTemplate entity."""

    user_id: UUID


class DayTemplateUpdateSchema(BaseSchema):
    """API schema for DayTemplate update requests."""

    slug: str | None = None
    alarm: Optional["AlarmSchema"] = None
    icon: str | None = None
    routine_ids: list[UUID] | None = None

