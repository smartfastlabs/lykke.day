from dataclasses import dataclass, field
from enum import Enum

from .base import BaseValueObject


@dataclass(kw_only=True)
class UserSetting(BaseValueObject):
    template_defaults: list[str] = field(default_factory=lambda: ["default"] * 7)


class UserStatus(str, Enum):
    """Lifecycle status for a user/account record."""

    ACTIVE = "active"
    NEW_LEAD = "new-lead"

