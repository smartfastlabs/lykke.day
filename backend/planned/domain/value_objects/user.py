from pydantic import Field

from .base import BaseValueObject


class UserSetting(BaseValueObject):
    template_defaults: list[str] = Field(
        default_factory=lambda: ["default"] * 7,
    )

