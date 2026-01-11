from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

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


@dataclass(kw_only=True)
class DayContext(BaseValueObject):
    day: "DayEntity"
    calendar_entries: list["CalendarEntryEntity"] = field(default_factory=list)
    tasks: list["TaskEntity"] = field(default_factory=list)
