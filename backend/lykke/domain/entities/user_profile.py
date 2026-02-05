"""Structured user profile aggregate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from lykke.domain.value_objects.update import UserProfileUpdateObject
from lykke.domain.value_objects.user_profile import WorkHours

from .base import BaseEntityObject

if TYPE_CHECKING:
    from lykke.domain.events.user_profile_events import UserProfileUpdatedEvent


@dataclass(kw_only=True)
class UserProfileEntity(
    BaseEntityObject[UserProfileUpdateObject, "UserProfileUpdatedEvent"]
):
    """Structured profile data for a user.

    This is intentionally *not* a Factoid: it is structured, typed, and intended
    for querying/feature logic. Onboarding writes here.
    """

    user_id: UUID
    preferred_name: str | None = None
    goals: list[str] = field(default_factory=list)
    work_hours: WorkHours | None = None
    onboarding_completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Generate deterministic UUID5 based on user_id (1:1 profile)."""
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            object.__setattr__(self, "id", self.id_from_user_id(self.user_id))

    @classmethod
    def id_from_user_id(cls, user_id: UUID) -> UUID:
        """Deterministic UUID5 for a user's profile."""
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.day.user_profile")
        return uuid.uuid5(namespace, str(user_id))

    def update(self, update_object: UserProfileUpdateObject) -> "UserProfileEntity":
        """Apply structured updates and record a domain event."""
        from lykke.domain.events.user_profile_events import UserProfileUpdatedEvent

        return super().apply_update(update_object, UserProfileUpdatedEvent)

