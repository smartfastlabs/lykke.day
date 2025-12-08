from datetime import UTC, date as dt_date, datetime, time
from zoneinfo import ZoneInfo

from gcsa.event import Event as GoogleEvent
from pydantic import Field, computed_field

from planned import settings

from .base import BaseDateObject
from .person import Person
from .task import TaskFrequency


def get_datetime(
    value: dt_date | datetime | None,
    use_start_of_day: bool = True,
) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC).astimezone(ZoneInfo(settings.TIMEZONE))

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
            starts_at=get_datetime(google_event.start),  # type: ignore
            ends_at=get_datetime(google_event.end),
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
