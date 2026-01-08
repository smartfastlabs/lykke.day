import uuid
from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from gcsa.event import Event as GoogleEvent

from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject


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


@dataclass(kw_only=True)
class CalendarEntryEntity(BaseEntityObject):
    user_id: UUID
    name: str
    calendar_id: UUID
    platform_id: str
    platform: str
    status: str
    starts_at: datetime
    frequency: value_objects.TaskFrequency
    category: value_objects.EventCategory | None = None
    ends_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    actions: list[value_objects.Action] = field(default_factory=list)
    timezone: str | None = field(default=None, repr=False)
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Ensure deterministic ID based on platform source."""
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            generated_id = self.id_from_platform(self.platform, self.platform_id)
            object.__setattr__(self, "id", generated_id)

    @classmethod
    def id_from_platform(cls, platform: str, platform_id: str) -> UUID:
        """Generate stable UUID5 using platform and platform-specific ID."""
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.calendar_entry")
        name = f"{platform}:{platform_id}"
        return uuid.uuid5(namespace, name)

    @property
    def date(self) -> dt_date:
        """Get the date for this calendar entry."""
        dt = self.starts_at
        user_timezone = ZoneInfo(settings.TIMEZONE)
        return dt.astimezone(user_timezone).date()

    @classmethod
    def from_google(
        cls,
        user_id: UUID,
        calendar_id: UUID,
        google_event: GoogleEvent,
        frequency: value_objects.TaskFrequency,
        target_timezone: str,
        category: value_objects.EventCategory | None = None,
    ) -> "CalendarEntryEntity":
        """Create a CalendarEntry from a Google Calendar event.

        Args:
            user_id: User ID for the calendar entry
            calendar_id: ID of the calendar
            google_event: Google Calendar event object
            frequency: Task frequency for the calendar entry
            target_timezone: Preferred display timezone (used as fallback when event lacks tz)
        """
        event_timezone = google_event.timezone or target_timezone

        # Convert datetimes to UTC for storage
        starts_at_utc = get_datetime(
            google_event.start,
            event_timezone,
            "UTC",
        )
        ends_at_utc = (
            get_datetime(
                google_event.end,
                event_timezone,
                "UTC",
            )
            if google_event.end
            else None
        )

        calendar_entry = cls(
            user_id=user_id,
            frequency=frequency,
            calendar_id=calendar_id,
            status=google_event.other.get("status", "NA"),
            name=google_event.summary,
            starts_at=starts_at_utc,
            ends_at=ends_at_utc,
            platform_id=google_event.id or "NA",
            platform="google",
            created_at=google_event.created.astimezone(UTC),
            updated_at=google_event.updated.astimezone(UTC),
            timezone=event_timezone,
            category=category,
        )
        return calendar_entry
