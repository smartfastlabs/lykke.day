from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from .. import value_objects
from .base import BaseEntityObject


class User(BaseEntityObject):
    """User entity compatible with fastapi-users."""

    email: str
    phone_number: str | None = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    settings: value_objects.UserSetting = Field(default_factory=value_objects.UserSetting)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
