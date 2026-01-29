from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from .ai_chat import LLMProvider
from .base import BaseValueObject
from .day import AlarmPreset


@dataclass(kw_only=True)
class UserSetting(BaseValueObject):
    template_defaults: list[str] = field(default_factory=lambda: ["default"] * 7)
    llm_provider: LLMProvider | None = None  # LLM provider for smart notifications
    timezone: str | None = None
    base_personality_slug: str = "default"
    llm_personality_amendments: list[str] = field(default_factory=list)
    morning_overview_time: str | None = None  # HH:MM format in user's local timezone
    alarm_presets: list[AlarmPreset] = field(default_factory=list)
    voice_setting: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.llm_provider, str):
            self.llm_provider = LLMProvider(self.llm_provider)
        raw_presets = cast("list[Any]", self.alarm_presets)
        if raw_presets:
            normalized: list[AlarmPreset] = []
            for preset in raw_presets:
                if isinstance(preset, AlarmPreset):
                    normalized.append(preset)
                elif hasattr(preset, "model_dump"):
                    normalized.append(AlarmPreset.from_dict(preset.model_dump()))
                elif isinstance(preset, dict):
                    normalized.append(AlarmPreset.from_dict(preset))
            self.alarm_presets = normalized


class UserStatus(str, Enum):
    """Lifecycle status for a user/account record."""

    ACTIVE = "active"
    NEW_LEAD = "new-lead"
