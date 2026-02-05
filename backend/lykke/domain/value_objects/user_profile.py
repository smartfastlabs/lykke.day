"""Value objects for structured user profile data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import cast

from .base import BaseValueObject
from .routine_definition import DayOfWeek


@dataclass(kw_only=True)
class WorkHours(BaseValueObject):
    """Typical work hours for a user.

    Kept intentionally small and structured; can be expanded as onboarding evolves.
    """

    start_time: time | None = None
    end_time: time | None = None
    weekdays: list[DayOfWeek] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Normalize times from strings if needed (JSONB round-trips).
        raw_start = cast("object", self.start_time)
        if isinstance(raw_start, str):
            try:
                self.start_time = time.fromisoformat(raw_start)
            except ValueError:
                self.start_time = None
        raw_end = cast("object", self.end_time)
        if isinstance(raw_end, str):
            try:
                self.end_time = time.fromisoformat(raw_end)
            except ValueError:
                self.end_time = None

        # Normalize weekdays into DayOfWeek enums.
        normalized: list[DayOfWeek] = []
        for raw in cast("list[object]", list(self.weekdays or [])):
            if isinstance(raw, DayOfWeek):
                normalized.append(raw)
                continue
            if isinstance(raw, int):
                try:
                    normalized.append(DayOfWeek(raw))
                except ValueError:
                    continue
                continue
            if isinstance(raw, str):
                try:
                    normalized.append(DayOfWeek(int(raw)))
                except (ValueError, TypeError):
                    continue
        self.weekdays = normalized

