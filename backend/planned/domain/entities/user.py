from datetime import UTC, datetime

from pydantic import Field

from ..value_objects.user import UserSetting
from .base import BaseEntityObject


class User(BaseEntityObject):
    username: str
    email: str
    phone_number: str | None = None
    password_hash: str
    settings: UserSetting = Field(default_factory=UserSetting)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
