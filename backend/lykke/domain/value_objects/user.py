from dataclasses import dataclass, field
from enum import Enum

from .ai_chat import LLMProvider
from .base import BaseValueObject


@dataclass(kw_only=True)
class UserSetting(BaseValueObject):
    template_defaults: list[str] = field(default_factory=lambda: ["default"] * 7)
    llm_provider: LLMProvider | None = None  # LLM provider for smart notifications
    timezone: str | None = None
    base_personality_slug: str = "default"

    def __post_init__(self) -> None:
        if isinstance(self.llm_provider, str):
            self.llm_provider = LLMProvider(self.llm_provider)


class UserStatus(str, Enum):
    """Lifecycle status for a user/account record."""

    ACTIVE = "active"
    NEW_LEAD = "new-lead"
