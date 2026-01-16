from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from .base import BaseValueObject

if TYPE_CHECKING:
    from ..entities import CalendarEntryEntity, DayEntity, TaskEntity


class DayTag(str, Enum):
    WEEKEND = "WEEKEND"
    VACATION = "VACATION"
    WORKDAY = "WORKDAY"


class DayStatus(str, Enum):
    UNSCHEDULED = "UNSCHEDULED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class DayMode(str, Enum):
    PRE_DAY = "PRE_DAY"
    LYKKE = "LYKKE"
    WORK = "WORK"
    POST_DAY = "POST_DAY"


class GoalStatus(str, Enum):
    """Status of a goal."""

    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    PUNT = "PUNT"


@dataclass(kw_only=True)
class Goal(BaseValueObject):
    """Goal value object representing a day-specific goal."""

    id: UUID = field(default_factory=uuid4)
    name: str
    status: GoalStatus = GoalStatus.INCOMPLETE
    created_at: datetime | None = field(default=None)


@dataclass(kw_only=True)
class DayContext(BaseValueObject):
    day: "DayEntity"
    calendar_entries: list["CalendarEntryEntity"] = field(default_factory=list)
    tasks: list["TaskEntity"] = field(default_factory=list)
