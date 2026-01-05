"""Domain events related to User aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from planned.domain.value_objects.update import UserUpdateObject

from .base import DomainEvent, EntityUpdatedEvent


@dataclass(frozen=True, kw_only=True)
class UserUpdatedEvent(EntityUpdatedEvent[UserUpdateObject]):
    """Event raised when a user is updated via apply_update()."""

