"""Structured onboarding value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from .base import BaseValueObject
from .user_profile import WorkHours


@dataclass(kw_only=True)
class OnboardingProfile(BaseValueObject):
    """Typed data collected during onboarding (incremental)."""

    preferred_name: str | None = None
    timezone: str | None = None  # IANA timezone name
    morning_overview_time: time | None = None  # local time
    goals: list[str] = field(default_factory=list)
    work_hours: WorkHours | None = None
    base_personality_slug: str | None = None
    llm_personality_amendments: list[str] = field(default_factory=list)

