from dataclasses import dataclass, field
from datetime import datetime as dt_datetime, time as dt_time
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

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


class AlarmType(str, Enum):
    """Type of alarm behavior."""

    URL = "URL"
    GENERIC = "GENERIC"


class AlarmStatus(str, Enum):
    """Status of an alarm."""

    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    SNOOZED = "SNOOZED"
    CANCELLED = "CANCELLED"


@dataclass(kw_only=True)
class Alarm(BaseValueObject):
    """Alarm value object representing a day or template alarm."""

    id: UUID = field(default_factory=uuid4)
    name: str
    time: dt_time
    datetime: dt_datetime | None = None
    type: AlarmType = AlarmType.URL
    url: str = ""
    status: AlarmStatus = AlarmStatus.ACTIVE
    snoozed_until: dt_datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Alarm":
        """Create an Alarm from a JSON-style dict."""
        alarm_time = data["time"]
        if isinstance(alarm_time, str):
            alarm_time = dt_time.fromisoformat(alarm_time)

        alarm_datetime = data.get("datetime")
        if isinstance(alarm_datetime, str):
            alarm_datetime = dt_datetime.fromisoformat(
                alarm_datetime.replace("Z", "+00:00")
            )

        alarm_type = data["type"]
        if isinstance(alarm_type, str):
            alarm_type = AlarmType(alarm_type)

        alarm_id = data.get("id")
        if isinstance(alarm_id, str):
            alarm_id = UUID(alarm_id)
        if alarm_id is None:
            alarm_key = f"alarm:{data['name']}:{alarm_time.isoformat()}:{alarm_type.value}:{data.get('url', '')}"
            alarm_id = uuid5(NAMESPACE_DNS, alarm_key)

        alarm_status = data.get("status", AlarmStatus.ACTIVE)
        if isinstance(alarm_status, str):
            alarm_status = AlarmStatus(alarm_status)

        snoozed_until = data.get("snoozed_until")
        if isinstance(snoozed_until, str):
            snoozed_until = dt_datetime.fromisoformat(
                snoozed_until.replace("Z", "+00:00")
            )

        return cls(
            id=alarm_id or uuid4(),
            name=data["name"],
            time=alarm_time,
            datetime=alarm_datetime,
            type=alarm_type,
            url=data.get("url", ""),
            status=alarm_status,
            snoozed_until=snoozed_until,
        )


@dataclass(kw_only=True)
class AlarmPreset(BaseValueObject):
    """Alarm preset stored in user settings."""

    id: UUID = field(default_factory=uuid4)
    name: str | None = None
    time: dt_time | None = None
    type: AlarmType = AlarmType.URL
    url: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlarmPreset":
        """Create an AlarmPreset from a JSON-style dict."""
        alarm_time = data.get("time")
        if isinstance(alarm_time, str):
            alarm_time = dt_time.fromisoformat(alarm_time)

        alarm_type = data.get("type", AlarmType.URL)
        if isinstance(alarm_type, str):
            alarm_type = AlarmType(alarm_type)

        alarm_id = data.get("id")
        if isinstance(alarm_id, str):
            alarm_id = UUID(alarm_id)

        return cls(
            id=alarm_id or uuid4(),
            name=data.get("name"),
            time=alarm_time,
            type=alarm_type,
            url=data.get("url", ""),
        )


class BrainDumpStatus(str, Enum):
    """Status of a brain dump."""

    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    PUNT = "PUNT"


class BrainDumpType(str, Enum):
    """Type of a brain dump."""

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
