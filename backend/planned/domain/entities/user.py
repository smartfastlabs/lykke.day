from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field, computed_field

from ..value_objects.user import UserSetting
from .base import BaseEntityObject


class User(BaseEntityObject):
    email: str
    password_hash: str
    settings: UserSetting = Field(default_factory=UserSetting)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @computed_field
    @property
    def uuid(self) -> UUID:
        """Return the user's ID as a UUID."""
        return UUID(self.id)

