from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from lykke.domain import value_objects
from lykke.domain.value_objects.update import UserUpdateObject

from .base import BaseEntityObject

if TYPE_CHECKING:
    from uuid import UUID

    from lykke.domain.events.user_events import UserUpdatedEvent


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
    default_conversation_id: UUID | None = None
    sms_conversation_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Ensure settings maintains the UserSetting dataclass invariant."""
        if isinstance(self.settings, dict):
            self.settings = value_objects.UserSetting.from_dict(self.settings)

    @property
    def user_id(self) -> UUID:
        """Alias user_id to id for domain event consistency."""
        return self.id

    def apply_update(
        self,
        update_object: UserUpdateObject,
        update_event_class: type[UserUpdatedEvent],
    ) -> UserEntity:
        """Apply updates ensuring settings remain a UserSetting dataclass."""
        # Extract non-None fields from update object without converting nested dataclasses to dicts
        update_dict: dict[str, Any] = {
            k: v
            for k, v in update_object.__dict__.items()
            if v is not None and k != "settings_update"
        }

        # Merge settings updates in the domain (presentation should pass intent only).
        if update_object.settings_update is not None:
            update_dict["settings"] = update_object.settings_update.merge(self.settings)

        updated_entity: UserEntity = self.clone(**update_dict)
        updated_entity = updated_entity.clone(updated_at=datetime.now(UTC))

        event = update_event_class(update_object=update_object, user_id=self.id)
        updated_entity._add_event(event)
        return updated_entity

    def create(self) -> UserEntity:
        """Mark this user as newly created with a user-scoped event."""
        from lykke.domain.events.base import EntityCreatedEvent

        self._add_event(EntityCreatedEvent(user_id=self.id))
        return self

    def delete(self) -> UserEntity:
        """Mark this user for deletion with a user-scoped event."""
        from lykke.domain.events.base import EntityDeletedEvent

        self._add_event(EntityDeletedEvent(user_id=self.id))
        return self
