from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from ..value_objects.user import UserSetting
from .base import BaseEntityObject


class User(BaseEntityObject):
    """User entity compatible with fastapi-users.

    Uses 'id' as an alias for 'uuid' and 'hashed_password' instead of 'password_hash'
    to match fastapi-users conventions.

    For backward compatibility, 'uuid' and 'password_hash' aliases are provided.
    These will be removed in a future migration step.
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

    # fastapi-users compatibility: 'id' as alias for 'uuid'
    @property
    def id(self) -> UUID:
        """fastapi-users compatibility alias for 'uuid'."""
        return self.uuid

    # Backward compatibility property (to be removed in future migration step)
    @property
    def password_hash(self) -> str:
        """Backward compatibility alias for 'hashed_password'."""
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        """Backward compatibility setter for 'hashed_password'."""
        self.hashed_password = value
