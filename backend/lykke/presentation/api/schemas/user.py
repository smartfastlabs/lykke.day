"""User response schemas."""

from datetime import datetime, time
from uuid import UUID

from pydantic import Field, field_validator

from lykke.core.utils.phone_numbers import normalize_phone_number
from lykke.domain.value_objects import (
    CalendarEntryNotificationChannel,
    LLMProvider,
    UserStatus,
)

from .alarm import AlarmPresetSchema
from .base import BaseSchema


class CalendarEntryNotificationRuleSchema(BaseSchema):
    """Schema for a single calendar entry notification rule."""

    channel: CalendarEntryNotificationChannel
    minutes_before: int = 0


class CalendarEntryNotificationSettingsSchema(BaseSchema):
    """Schema for calendar entry notification settings."""

    enabled: bool = True
    rules: list[CalendarEntryNotificationRuleSchema] = Field(default_factory=list)


class UserSettingsSchema(BaseSchema):
    """Schema for user settings."""

    template_defaults: list[str]
    llm_provider: LLMProvider | None = None
    timezone: str | None = None
    base_personality_slug: str = "default"
    llm_personality_amendments: list[str] = Field(default_factory=list)
    morning_overview_time: time | None = None  # HH:MM format in user's local timezone
    alarm_presets: list[AlarmPresetSchema] = Field(default_factory=list)
    calendar_entry_notification_settings: CalendarEntryNotificationSettingsSchema


class UserSchema(BaseSchema):
    """Schema for the current authenticated user."""

    id: UUID
    email: str
    phone_number: str | None = None
    status: UserStatus
    is_active: bool
    is_superuser: bool
    is_verified: bool
    settings: UserSettingsSchema
    created_at: datetime
    updated_at: datetime | None = None


class UserSettingsUpdateSchema(BaseSchema):
    """Schema for updating user settings."""

    template_defaults: list[str] | None = Field(
        default=None, min_length=7, max_length=7
    )
    llm_provider: LLMProvider | None = None
    timezone: str | None = None
    base_personality_slug: str | None = None
    llm_personality_amendments: list[str] | None = None
    morning_overview_time: time | None = None  # HH:MM format in user's local timezone
    alarm_presets: list[AlarmPresetSchema] | None = None
    calendar_entry_notification_settings: (
        CalendarEntryNotificationSettingsSchema | None
    ) = None


class UserUpdateSchema(BaseSchema):
    """Schema for updating a user profile."""

    phone_number: str | None = None
    status: UserStatus | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    settings: UserSettingsUpdateSchema | None = None

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone_number_input(cls, v: str | None) -> str | None:
        if v is None:
            return None
        normalized = normalize_phone_number(v)
        return normalized or None
