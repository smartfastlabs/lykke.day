"""Value objects for UserCheckIn entity."""

from __future__ import annotations

from enum import Enum


class UserCheckInSource(str, Enum):
    """Who or what created the check-in."""

    USER = "user"
    LLM_USE_CASE = "llm_use_case"
    SYSTEM = "system"
