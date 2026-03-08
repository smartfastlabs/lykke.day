"""Value objects for UserCheckIn entity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .base import BaseValueObject


class UserCheckInSource(str, Enum):
    """Who or what created the check-in."""

    USER = "user"
    LLM_USE_CASE = "llm_use_case"
    SYSTEM = "system"


@dataclass(kw_only=True)
class CheckInScoreStats(BaseValueObject):
    """Per-key score statistics derived from check-ins."""

    key: str
    count: int
    mean: float
    median: float
    min: float
    max: float
    stddev: float
