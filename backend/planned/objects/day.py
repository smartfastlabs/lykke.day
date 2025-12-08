from datetime import date as dt_date, datetime, time
from enum import Enum

from pydantic import BaseModel, Field

from .alarm import Alarm
from .base import BaseObject
from .event import Event
from .message import Message
from .task import Task


class DayTemplate(BaseObject):
    tasks: list[str] = Field(default_factory=list)
    alarm: Alarm | None = None


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


class Day(BaseObject):
    date: dt_date
    template_id: str = "default"
    tags: list[DayTag] = Field(default_factory=list)
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        self.id = str(self.date)


class DayContext(BaseModel):
    day: Day
    events: list[Event] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
