from dataclasses import dataclass, field

from .base import BaseValueObject


@dataclass(kw_only=True)
class HighLevelPlan(BaseValueObject):
    title: str | None = None
    text: str | None = None
    intentions: list[str] = field(default_factory=list)
