"""User response schemas."""

from datetime import datetime
from uuid import UUID

from lykke.domain.value_objects import UserStatus

from .base import BaseSchema


class UserSettingsSchema(BaseSchema):
    """Schema for user settings."""

    template_defaults: list[str]


class UserSchema(BaseSchema):
    """Schema for the current authenticated user."""

    id: UUID
    email: str | None = None
    phone_number: str | None = None
    status: UserStatus
    is_active: bool
    is_superuser: bool
    is_verified: bool
    settings: UserSettingsSchema
    created_at: datetime
    updated_at: datetime | None = None

