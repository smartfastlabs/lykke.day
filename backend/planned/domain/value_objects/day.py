from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..entities.calendar_entry import CalendarEntry
    from ..entities.day import Day
    from ..entities.message import Message
    from ..entities.task import Task


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
    day: "Day"
    calendar_entries: list["CalendarEntry"] = Field(default_factory=list)
    tasks: list["Task"] = Field(default_factory=list)
    messages: list["Message"] = Field(default_factory=list)


def _rebuild_day_context() -> None:
    """Rebuild DayContext model after all entity classes are defined."""
    # These imports are here to rebuild the model after all entities are defined

    DayContext.model_rebuild()

