from datetime import UTC, date as dt_date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from gcsa.event import Event as GoogleEvent
from pydantic import Field

from ..value_objects.task import TaskFrequency
from .action import Action
from .base import BaseDateObject
from .person import Person


def get_datetime(
    value: dt_date | datetime,
    source_timezone: str,
    target_timezone: str,
    use_start_of_day: bool = True,
) -> datetime:
    """Convert a date or datetime to a datetime in the target timezone.
    
    Args:
        value: Date or datetime to convert
        source_timezone: Timezone of the source value (if naive datetime or date)
        target_timezone: Target timezone for the result
        use_start_of_day: If value is a date, use start (True) or end (False) of day
    """
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            # Datetime already has timezone info, just convert to target
            return value.astimezone(ZoneInfo(target_timezone))
        # Naive datetime, assume it's in the source timezone
        return value.replace(tzinfo=ZoneInfo(source_timezone)).astimezone(
            ZoneInfo(target_timezone)
        )
    return datetime.combine(
        value,
        time(0, 0, 0) if use_start_of_day else time(23, 59, 59),
        tzinfo=ZoneInfo(target_timezone),
    )


class Event(BaseDateObject):
    user_uuid: UUID
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
        user_uuid: UUID,
        calendar_id: str,
        google_event: GoogleEvent,
        frequency: TaskFrequency,
        target_timezone: str,
    ) -> "Event":
        """Create an Event from a Google Calendar event.
        
        Args:
            user_uuid: User UUID for the event
            calendar_id: ID of the calendar
            google_event: Google Calendar event object
            frequency: Task frequency for the event
            target_timezone: Target timezone for datetime conversion
        """
        event = cls(
            user_uuid=user_uuid,
            id=f"google:{google_event.id}",
            frequency=frequency,
            calendar_id=calendar_id,
            status=google_event.other.get("status", "NA"),
            name=google_event.summary,
            starts_at=get_datetime(
                google_event.start,
                google_event.timezone,
                target_timezone,
            ),
            ends_at=get_datetime(
                google_event.end,
                google_event.timezone,
                target_timezone,
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
            timezone=target_timezone,
        )
        return event
