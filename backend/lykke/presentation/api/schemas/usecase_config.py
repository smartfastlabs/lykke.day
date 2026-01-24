"""UseCase config schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntitySchema, BaseSchema


class UseCaseConfigSchema(BaseEntitySchema):
    """UseCase config schema."""

    user_id: UUID
    usecase: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None = None


class UseCaseConfigCreateSchema(BaseSchema):
    """API schema for creating/updating a usecase config."""

    usecase: str
    config: dict[str, Any]


class NotificationUseCaseConfigSchema(BaseSchema):
    """Schema for notification usecase config (typed)."""

    user_amendments: list[str] = Field(default_factory=list)
    rendered_prompt: str | None = None
