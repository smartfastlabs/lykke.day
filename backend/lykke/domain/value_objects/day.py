from dataclasses import dataclass, field
from datetime import datetime as dt_datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from .base import BaseValueObject

if TYPE_CHECKING:
    from lykke.domain.entities import (
        BrainDumpEntity,
        CalendarEntryEntity,
        DayEntity,
        FactoidEntity,
        MessageEntity,
        PushNotificationEntity,
        RoutineEntity,
        TaskEntity,
    )


class DayTag(str, Enum):
    WEEKEND = "WEEKEND"
    VACATION = "VACATION"
    WORKDAY = "WORKDAY"


class DayStatus(str, Enum):
    UNSCHEDULED = "UNSCHEDULED"
    SCHEDULED = "SCHEDULED"
    STARTED = "STARTED"
    COMPLETE = "COMPLETE"


class DayMode(str, Enum):
    PRE_DAY = "PRE_DAY"
    LYKKE = "LYKKE"
    WORK = "WORK"
    POST_DAY = "POST_DAY"


class ReminderStatus(str, Enum):
    """Status of a reminder."""

    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    PUNT = "PUNT"


@dataclass(kw_only=True)
class Reminder(BaseValueObject):
    """Reminder value object representing a day-specific reminder."""

    id: UUID = field(default_factory=uuid4)
    name: str
    status: ReminderStatus = ReminderStatus.INCOMPLETE
    created_at: dt_datetime | None = field(default=None)


class AlarmType(str, Enum):
    """Type of alarm behavior."""

    URL = "URL"
    GENERIC = "GENERIC"


@dataclass(kw_only=True)
class Alarm(BaseValueObject):
    """Alarm value object representing a day or template alarm."""

    name: str
    time: time
    datetime: dt_datetime | None = None
    type: AlarmType = AlarmType.URL
    url: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Alarm":
        """Create an Alarm from a JSON-style dict."""
        alarm_time = data["time"]
        if isinstance(alarm_time, str):
            alarm_time = time.fromisoformat(alarm_time)

        alarm_datetime = data.get("datetime")
        if isinstance(alarm_datetime, str):
            alarm_datetime = dt_datetime.fromisoformat(
                alarm_datetime.replace("Z", "+00:00")
            )

        alarm_type = data["type"]
        if isinstance(alarm_type, str):
            alarm_type = AlarmType(alarm_type)

        return cls(
            name=data["name"],
            time=alarm_time,
            datetime=alarm_datetime,
            type=alarm_type,
            url=data.get("url", ""),
        )


class BrainDumpItemStatus(str, Enum):
    """Status of a brain dump item."""

    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    PUNT = "PUNT"


class BrainDumpItemType(str, Enum):
    """Type of a brain dump item."""

    GENERAL = "GENERAL"
    COMMAND = "COMMAND"


@dataclass(kw_only=True)
class DayContext(BaseValueObject):
    day: "DayEntity"
    calendar_entries: list["CalendarEntryEntity"] = field(default_factory=list)
    tasks: list["TaskEntity"] = field(default_factory=list)
    routines: list["RoutineEntity"] = field(default_factory=list)
    brain_dump_items: list["BrainDumpEntity"] = field(default_factory=list)


@dataclass(kw_only=True)
class LLMPromptContext(DayContext):
    """Expanded context for LLM prompts."""

    factoids: list["FactoidEntity"] = field(default_factory=list)
    messages: list["MessageEntity"] = field(default_factory=list)
    push_notifications: list["PushNotificationEntity"] = field(default_factory=list)
