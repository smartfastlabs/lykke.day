"""UseCase config value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseValueObject


@dataclass(kw_only=True)
class NotificationUseCaseConfig(BaseValueObject):
    """Configuration for the notification usecase."""

    user_amendments: list[str] = field(default_factory=list)
