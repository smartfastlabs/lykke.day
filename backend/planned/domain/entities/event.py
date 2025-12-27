from datetime import UTC, date as dt_date, datetime, time
from zoneinfo import ZoneInfo

from gcsa.event import Event as GoogleEvent
from pydantic import Field

from planned.core.config import settings

from .action import Action
from .base import BaseDateObject
from .person import Person
from .task import TaskFrequency


def get_datetime(
    value: dt_date | datetime,
    timezone: str,
    use_start_of_day: bool = True,
) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            # Datetime already has timezone info, just convert to target
            return value.astimezone(ZoneInfo(settings.TIMEZONE))
        # Naive datetime, assume it's in the given timezone
        return value.replace(tzinfo=ZoneInfo(timezone)).astimezone(
            ZoneInfo(settings.TIMEZONE)
        )
    return datetime.combine(
        value,
        time(0, 0, 0) if use_start_of_day else time(23, 59, 59),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )


class Event(BaseDateObject):
    name: str
    calendar_id: str
    platform_id: str
    platform: str
    status: str
    starts_at: datetime
    frequency: TaskFrequency
    ends_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    people: list[Person] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)

    def _get_datetime(self) -> datetime:
        return self.starts_at

    @classmethod
    def from_google(
        cls,
        calendar_id: str,
        google_event: GoogleEvent,
        frequency: TaskFrequency,
    ) -> "Event":
        event = cls(
            id=f"google:{google_event.id}",
            frequency=frequency,
            calendar_id=calendar_id,
            status=google_event.other.get("status", "NA"),
            name=google_event.summary,
            starts_at=get_datetime(
                google_event.start,
                google_event.timezone,
            ),
            ends_at=get_datetime(
                google_event.end,
                google_event.timezone,
            )
            if google_event.end
            else None,
            platform_id=google_event.id or "NA",
            platform="google",
            created_at=google_event.created.astimezone(UTC).replace(tzinfo=None),
            updated_at=google_event.updated.astimezone(UTC).replace(tzinfo=None),
            people=[
                Person(
                    name=a.display_name or None,
                    email=a.email,
                )
                for a in google_event.attendees
            ],
        )
        return event
