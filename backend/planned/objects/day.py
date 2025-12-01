from datetime import date as dt_date, datetime, time
from enum import Enum

from pydantic import BaseModel, Field

from .alarm import Alarm
from .base import BaseObject
from .event import Event
from .message import Message
from .task import Task


class DayTag(str, Enum):
    WEEKEND = "WEEKEND"
    VACATION = "VACATION"
    WORKDAY = "WORKDAY"


class DayStatus(str, Enum):
    UNSCHEDULED = "UNSCHEDULED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class Day(BaseObject):
    date: dt_date
    tags: list[DayTag] = Field(default_factory=list)
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None
    alarms: list[Alarm] = Field(default_factory=list)


class DayContext(BaseModel):
    date: dt_date
    day: Day
    events: list[Event]
    tasks: list[Task]
    messages: list[Message]
