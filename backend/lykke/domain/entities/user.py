from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .. import value_objects
from ..value_objects.update import UserUpdateObject
from .base import BaseEntityObject

if TYPE_CHECKING:
    from ..events.user_events import UserUpdatedEvent


@dataclass(kw_only=True)
class UserEntity(BaseEntityObject[UserUpdateObject, "UserUpdatedEvent"]):
    """User entity compatible with fastapi-users."""

    email: str
    phone_number: str | None = None
    hashed_password: str
    status: value_objects.UserStatus = value_objects.UserStatus.ACTIVE
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    settings: value_objects.UserSetting = field(
        default_factory=value_objects.UserSetting
    )
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Ensure settings maintains the UserSetting dataclass invariant."""
        if isinstance(self.settings, dict):
            self.settings = value_objects.UserSetting(**self.settings)

    def apply_update(
        self,
        update_object: UserUpdateObject,
        update_event_class: type[UserUpdatedEvent],
    ) -> UserEntity:
        """Apply updates ensuring settings remain a UserSetting dataclass."""
        # Extract non-None fields from update object without converting nested dataclasses to dicts
        update_dict: dict[str, Any] = {
            k: v for k, v in update_object.__dict__.items() if v is not None
        }
        
        # No need to reconstruct settings since __dict__ preserves the dataclass instance

        updated_entity: UserEntity = self.clone(**update_dict)
        updated_entity = updated_entity.clone(updated_at=datetime.now(UTC))

        event = update_event_class(update_object=update_object)
        updated_entity._add_event(event)
        return updated_entity
