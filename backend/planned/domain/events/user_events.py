"""Domain events related to User aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from planned.domain.value_objects.update import UserUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from planned.domain.entities.user import UserEntity


@dataclass(frozen=True, kw_only=True)
class UserUpdatedEvent(EntityUpdatedEvent[UserUpdateObject, "UserEntity"]):
    """Event raised when a user is updated via apply_update()."""

