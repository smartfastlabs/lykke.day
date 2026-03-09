from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import time
from enum import Enum
from typing import Any, cast

from .ai_chat import LLMProvider
from .base import BaseRequestObject, BaseValueObject
from .day import AlarmPreset


class CalendarEntryNotificationChannel(str, Enum):
    """Notification delivery channel for calendar entry reminders."""

    PUSH = "PUSH"
    TEXT = "TEXT"
    KIOSK_ALARM = "KIOSK_ALARM"


@dataclass(kw_only=True)
class CalendarEntryNotificationRule(BaseValueObject):
    """Single reminder rule for calendar entries."""

    channel: CalendarEntryNotificationChannel
    minutes_before: int = 0

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CalendarEntryNotificationRule":
        channel: CalendarEntryNotificationChannel | str | None = data.get("channel")
        if isinstance(channel, str):
            try:
                channel = CalendarEntryNotificationChannel(channel)
            except ValueError:
                channel = CalendarEntryNotificationChannel.PUSH
        if not isinstance(channel, CalendarEntryNotificationChannel):
            channel = CalendarEntryNotificationChannel.PUSH
        minutes_before = data.get("minutes_before", 0)
        try:
            minutes_before = int(minutes_before)
        except (TypeError, ValueError):
            minutes_before = 0
        if minutes_before < 0:
            minutes_before = 0
        return cls(
            channel=channel,
            minutes_before=minutes_before,
        )


def _default_calendar_entry_notification_rules() -> list[CalendarEntryNotificationRule]:
    return [
        CalendarEntryNotificationRule(
            channel=CalendarEntryNotificationChannel.TEXT,
            minutes_before=10,
        ),
        CalendarEntryNotificationRule(
            channel=CalendarEntryNotificationChannel.PUSH,
            minutes_before=5,
        ),
        CalendarEntryNotificationRule(
            channel=CalendarEntryNotificationChannel.KIOSK_ALARM,
            minutes_before=0,
        ),
    ]


@dataclass(kw_only=True)
class CalendarEntryNotificationSettings(BaseValueObject):
    """Settings for calendar entry reminder notifications."""

    enabled: bool = True
    rules: list[CalendarEntryNotificationRule] = field(
        default_factory=_default_calendar_entry_notification_rules
    )

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any] | None
    ) -> "CalendarEntryNotificationSettings":
        if data is None:
            return cls()
        enabled = data.get("enabled", True)
        raw_rules = data.get("rules", [])
        rules: list[CalendarEntryNotificationRule] = []
        if isinstance(raw_rules, list):
            for rule in raw_rules:
                if isinstance(rule, CalendarEntryNotificationRule):
                    rules.append(rule)
                elif hasattr(rule, "model_dump"):
                    rules.append(
                        CalendarEntryNotificationRule.from_dict(rule.model_dump())
                    )
                elif isinstance(rule, dict):
                    rules.append(CalendarEntryNotificationRule.from_dict(rule))
        return cls(enabled=bool(enabled), rules=rules)


@dataclass(kw_only=True)
class StatusSignalGoal(BaseValueObject):
    """Goal guidance for a status signal."""

    text: str = ""
    value: float | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "StatusSignalGoal":
        if data is None:
            return cls()
        raw_text = data.get("text", "")
        text = raw_text.strip() if isinstance(raw_text, str) else ""
        raw_value = data.get("value")
        value: float | None = None
        if raw_value is not None:
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                value = None
        return cls(text=text, value=value)


@dataclass(kw_only=True)
class StatusSignal(BaseValueObject):
    """User-defined signal tracked in status check-ins."""

    name: str
    slug: str
    description: str = ""
    goal: StatusSignalGoal = field(default_factory=StatusSignalGoal)

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = value.strip().lower()
        slug_chars: list[str] = []
        prev_dash = False
        for char in cleaned:
            if char.isalnum():
                slug_chars.append(char)
                prev_dash = False
            elif not prev_dash:
                slug_chars.append("-")
                prev_dash = True
        slug = "".join(slug_chars).strip("-")
        return slug

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StatusSignal | None":
        raw_name = data.get("name")
        if not isinstance(raw_name, str):
            return None
        name = raw_name.strip()
        if not name:
            return None
        raw_slug = data.get("slug")
        slug = raw_slug.strip() if isinstance(raw_slug, str) else ""
        slug = cls._slugify(slug or name)
        if not slug:
            return None
        raw_description = data.get("description", "")
        description = raw_description.strip() if isinstance(raw_description, str) else ""
        raw_goal = data.get("goal")
        goal: StatusSignalGoal
        if isinstance(raw_goal, StatusSignalGoal):
            goal = raw_goal
        elif isinstance(raw_goal, Mapping):
            goal = StatusSignalGoal.from_dict(raw_goal)
        else:
            goal = StatusSignalGoal()
        return cls(name=name, slug=slug, description=description, goal=goal)


def _default_status_signals() -> list[StatusSignal]:
    return [
        StatusSignal(
            name="Cravings",
            slug="cravings",
            description="Urge intensity and frequency.",
        ),
        StatusSignal(
            name="Depression",
            slug="depression",
            description="Low mood, hopelessness, and emotional heaviness.",
        ),
        StatusSignal(
            name="Anxiety",
            slug="anxiety",
            description="Stress, worry, and nervous system activation.",
        ),
        StatusSignal(
            name="Mood",
            slug="mood",
            description="Overall emotional tone for the day.",
        ),
        StatusSignal(
            name="Energy",
            slug="energy",
            description="Mental and physical energy availability.",
        ),
        StatusSignal(
            name="Focus",
            slug="focus",
            description="Attention quality and ability to stay on task.",
        ),
    ]


def _parse_morning_overview_time(value: Any) -> time | None:
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError:
            return None
    return None


@dataclass(kw_only=True)
class UserSetting(BaseValueObject):
    template_defaults: list[str] = field(default_factory=lambda: ["default"] * 7)
    llm_provider: LLMProvider | None = None  # LLM provider for smart notifications
    timezone: str | None = None
    base_personality_slug: str = "default"
    llm_personality_amendments: list[str] = field(default_factory=list)
    morning_overview_time: time | None = None  # HH:MM format in user's local timezone
    alarm_presets: list[AlarmPreset] = field(default_factory=list)
    calendar_entry_notification_settings: CalendarEntryNotificationSettings = field(
        default_factory=CalendarEntryNotificationSettings
    )
    status_signals: list[StatusSignal] = field(default_factory=_default_status_signals)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "UserSetting":
        """Parse a settings mapping into a UserSetting.

        This is the single canonical place for:
        - filtering unknown keys
        - normalizing nested fields (e.g. alarm_presets via __post_init__)
        """
        if data is None:
            return cls()

        allowed_keys = {field_info.name for field_info in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        if "morning_overview_time" in filtered:
            filtered["morning_overview_time"] = _parse_morning_overview_time(
                filtered["morning_overview_time"]
            )
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
        raw_calendar_settings: Any = self.calendar_entry_notification_settings
        if not isinstance(raw_calendar_settings, CalendarEntryNotificationSettings):
            if hasattr(raw_calendar_settings, "model_dump"):
                self.calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings.from_dict(
                        raw_calendar_settings.model_dump()
                    )
                )
            elif isinstance(raw_calendar_settings, dict):
                self.calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings.from_dict(raw_calendar_settings)
                )
            elif raw_calendar_settings is None:
                self.calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings()
                )
        raw_signals = cast("list[Any]", self.status_signals)
        if raw_signals:
            normalized_signals: list[StatusSignal] = []
            seen: set[str] = set()
            for signal in raw_signals:
                candidate: StatusSignal | None = None
                if isinstance(signal, StatusSignal):
                    candidate = signal
                elif hasattr(signal, "model_dump"):
                    candidate = StatusSignal.from_dict(signal.model_dump())
                elif isinstance(signal, Mapping):
                    candidate = StatusSignal.from_dict(signal)
                if candidate is None:
                    continue
                key = candidate.slug.casefold()
                if key in seen:
                    continue
                seen.add(key)
                normalized_signals.append(candidate)
            self.status_signals = normalized_signals or _default_status_signals()


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
        allowed_keys = {field_info.name for field_info in fields(UserSetting)}
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
        if "calendar_entry_notification_settings" in self.data:
            calendar_settings_raw = self.data.get("calendar_entry_notification_settings")
            if calendar_settings_raw is None:
                calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings(enabled=False, rules=[])
                )
            elif hasattr(calendar_settings_raw, "model_dump"):
                calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings.from_dict(
                        calendar_settings_raw.model_dump()
                    )
                )
            elif isinstance(calendar_settings_raw, dict):
                calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings.from_dict(calendar_settings_raw)
                )
            else:
                calendar_entry_notification_settings = (
                    CalendarEntryNotificationSettings.from_dict(None)
                )
        else:
            calendar_entry_notification_settings = (
                existing.calendar_entry_notification_settings
            )
        status_signals = (
            cast("list[Any]", self.data.get("status_signals"))
            if "status_signals" in self.data and self.data.get("status_signals") is not None
            else existing.status_signals
        )

        # morning_overview_time is special: explicit null should clear the value.
        if "morning_overview_time" in self.data:
            morning_overview_time = _parse_morning_overview_time(
                self.data.get("morning_overview_time")
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
            calendar_entry_notification_settings=calendar_entry_notification_settings,
            status_signals=cast("list[StatusSignal]", status_signals),
        )


class UserStatus(str, Enum):
    """Lifecycle status for a user/account record."""

    ACTIVE = "active"
    NEW_LEAD = "new-lead"
