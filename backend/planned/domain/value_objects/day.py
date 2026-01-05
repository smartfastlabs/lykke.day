from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

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


class DayContext(BaseModel):
    day: "DayEntity"
    calendar_entries: list["CalendarEntryEntity"] = Field(default_factory=list)
    tasks: list["TaskEntity"] = Field(default_factory=list)


def _rebuild_day_context() -> None:
    """Rebuild DayContext model after all entity classes are defined."""
    # These imports are here to rebuild the model after all entities are defined

    DayContext.model_rebuild()
