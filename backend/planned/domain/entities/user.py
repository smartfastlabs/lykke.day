from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from .. import value_objects
from .base import BaseEntityObject


@dataclass(kw_only=True)
class User(BaseEntityObject):
    """User entity compatible with fastapi-users."""

    email: str
    phone_number: str | None = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    settings: value_objects.UserSetting = field(default_factory=value_objects.UserSetting)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
