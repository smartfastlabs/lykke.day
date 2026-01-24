"""Domain events related to User aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from lykke.domain.value_objects.update import UserUpdateObject

from .base import DomainEvent, EntityUpdatedEvent

__all__ = ["UserForgotPasswordEvent", "UserUpdatedEvent"]


@dataclass(frozen=True, kw_only=True)
class UserUpdatedEvent(EntityUpdatedEvent[UserUpdateObject]):
    """Event raised when a user is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class UserForgotPasswordEvent(DomainEvent):
    """Event raised when a user requests a password reset."""

    email: str
    reset_token: str
    request_origin: str | None = None
    user_agent: str | None = None
