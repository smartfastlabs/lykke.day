"""User response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from lykke.domain.value_objects import UserStatus

from .base import BaseSchema


class UserSettingsSchema(BaseSchema):
    """Schema for user settings."""

    template_defaults: list[str]


class UserSchema(BaseSchema):
    """Schema for the current authenticated user."""

    id: UUID
    email: str
    phone_number: str | None = None
    status: UserStatus
    is_active: bool
    is_superuser: bool
    is_verified: bool
    settings: UserSettingsSchema
    default_conversation_id: UUID | None = None
    sms_conversation_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class UserSettingsUpdateSchema(BaseSchema):
    """Schema for updating user settings."""

    template_defaults: list[str] | None = Field(
        default=None, min_length=7, max_length=7
    )


class UserUpdateSchema(BaseSchema):
    """Schema for updating a user profile."""

    phone_number: str | None = None
    status: UserStatus | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    settings: UserSettingsUpdateSchema | None = None
    default_conversation_id: UUID | None = None
    sms_conversation_id: UUID | None = None

