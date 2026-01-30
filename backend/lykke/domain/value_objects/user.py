from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from .ai_chat import LLMProvider
from .base import BaseRequestObject, BaseValueObject
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "UserSetting":
        """Parse a settings mapping into a UserSetting.

        This is the single canonical place for:
        - filtering unknown keys
        - normalizing nested fields (e.g. alarm_presets via __post_init__)
        """
        if data is None:
            return cls()

        allowed_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)

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


@dataclass(kw_only=True)
class UserSettingUpdate(BaseRequestObject):
    """Partial settings update (PATCH-like).

    Carries only the fields the client provided (including explicit nulls),
    and knows how to merge into an existing UserSetting without wiping
    unspecified fields.
    """

    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "UserSettingUpdate":
        allowed_keys = set(UserSetting.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(data=dict(filtered))

    def merge(self, current: UserSetting | None) -> UserSetting:
        existing = current or UserSetting()

        # Preserve current values by default; only override when key is present.
        template_defaults = (
            self.data.get("template_defaults")
            if "template_defaults" in self.data
            and self.data.get("template_defaults") is not None
            else existing.template_defaults
        )
        llm_provider = (
            self.data.get("llm_provider")
            if "llm_provider" in self.data
            else existing.llm_provider
        )
        timezone = (
            self.data.get("timezone") if "timezone" in self.data else existing.timezone
        )
        base_personality_slug = (
            self.data.get("base_personality_slug")
            if "base_personality_slug" in self.data
            and self.data.get("base_personality_slug") is not None
            else existing.base_personality_slug
        )
        llm_personality_amendments = (
            self.data.get("llm_personality_amendments")
            if "llm_personality_amendments" in self.data
            and self.data.get("llm_personality_amendments") is not None
            else existing.llm_personality_amendments
        )
        alarm_presets = (
            cast("list[Any]", self.data.get("alarm_presets"))
            if "alarm_presets" in self.data
            and self.data.get("alarm_presets") is not None
            else existing.alarm_presets
        )

        # morning_overview_time is special: explicit null should clear the value.
        if "morning_overview_time" in self.data:
            morning_overview_time = cast(
                "str | None", self.data.get("morning_overview_time")
            )
        else:
            morning_overview_time = existing.morning_overview_time

        return UserSetting(
            template_defaults=cast("list[str]", template_defaults),
            llm_provider=cast("LLMProvider | None", llm_provider),
            timezone=cast("str | None", timezone),
            base_personality_slug=cast("str", base_personality_slug),
            llm_personality_amendments=cast("list[str]", llm_personality_amendments),
            morning_overview_time=morning_overview_time,
            alarm_presets=cast("list[AlarmPreset]", alarm_presets),
        )


class UserStatus(str, Enum):
    """Lifecycle status for a user/account record."""

    ACTIVE = "active"
    NEW_LEAD = "new-lead"
