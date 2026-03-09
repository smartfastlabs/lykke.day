"""UseCase config schemas."""

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import BaseEntitySchema, BaseSchema

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


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
    send_acknowledgment: bool | None = None


class UserStatusCheckInPreviewSchema(BaseSchema):
    """Schema for generated user status check-in previews."""

    text: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)
