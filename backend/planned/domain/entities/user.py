from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from ..value_objects.user import UserSetting
from .base import BaseEntityObject


class User(BaseEntityObject):
    """User entity compatible with fastapi-users.

    Uses 'hashed_password' instead of 'password_hash' to match fastapi-users conventions.
    """

    email: str
    phone_number: str | None = None
    hashed_password: str = Field(alias="password_hash")
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    settings: UserSetting = Field(default_factory=UserSetting)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
