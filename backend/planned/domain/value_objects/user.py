from dataclasses import dataclass, field

from .base import BaseValueObject


@dataclass(kw_only=True)
class UserSetting(BaseValueObject):
    template_defaults: list[str] = field(default_factory=lambda: ["default"] * 7)

