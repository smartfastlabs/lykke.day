from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from .base import BaseValueObject

if TYPE_CHECKING:
    from lykke.domain.entities import (
        BrainDumpEntity,
        CalendarEntryEntity,
        DayEntity,
        MessageEntity,
        PushNotificationEntity,
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
    created_at: datetime | None = field(default=None)


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
    brain_dump_items: list["BrainDumpEntity"] = field(default_factory=list)


@dataclass(kw_only=True)
class LLMPromptContext(DayContext):
    """Expanded context for LLM prompts."""

    messages: list["MessageEntity"] = field(default_factory=list)
    push_notifications: list["PushNotificationEntity"] = field(default_factory=list)
