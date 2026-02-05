"""Domain events for structured user profile changes."""

from __future__ import annotations

from dataclasses import dataclass

from lykke.domain.value_objects.update import UserProfileUpdateObject

from .base import EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class UserProfileUpdatedEvent(EntityUpdatedEvent[UserProfileUpdateObject]):
    """Event raised when a user profile is updated via apply_update()."""

