from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from ..value_objects.user import UserSetting
from .base import BaseEntityObject


class User(BaseEntityObject):
    email: str
    password_hash: str
    settings: UserSetting = Field(default_factory=UserSetting)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

