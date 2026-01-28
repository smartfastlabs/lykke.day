"""Mapper for converting Google Calendar events to domain entities."""

from datetime import UTC, date as dt_date, datetime, time
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity
from lykke.domain.entities.calendar_entry_series import CalendarEntrySeriesEntity


class GoogleEventLike(Protocol):
    """Protocol for Google Calendar event objects.

    This allows using either gcsa.event.Event or test stubs.
    """

    start: datetime | dt_date
    end: datetime | dt_date | None
    timezone: str | None
    summary: str
    id: str | None
    other: dict[str, Any]
    created: datetime
    updated: datetime


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
            return value.astimezone(ZoneInfo(target_timezone))
        return value.replace(tzinfo=ZoneInfo(source_timezone)).astimezone(
            ZoneInfo(target_timezone)
        )
    return datetime.combine(
        value,
        time(0, 0, 0) if use_start_of_day else time(23, 59, 59),
        tzinfo=ZoneInfo(target_timezone),
    )


class GoogleCalendarMapper:
    """Maps Google Calendar API objects to domain entities.

    This mapper isolates the infrastructure concern of translating between
    Google Calendar's data structures and our domain entities.
    """

    @staticmethod
    def to_calendar_entry(
        user_id: UUID,
        calendar_id: UUID,
        google_event: GoogleEventLike,
        frequency: value_objects.TaskFrequency,
        target_timezone: str,
        category: value_objects.EventCategory | None = None,
    ) -> CalendarEntryEntity:
        """Create a CalendarEntry from a Google Calendar event.

        Args:
            user_id: User ID for the calendar entry
            calendar_id: ID of the calendar
            google_event: Google Calendar event object (gcsa.event.Event or compatible)
            frequency: Task frequency for the calendar entry
            target_timezone: Preferred display timezone (used as fallback when event lacks tz)
            category: Optional event category
        """
        event_timezone = google_event.timezone or target_timezone

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

        series_platform_id = getattr(google_event, "recurring_event_id", None)
        if series_platform_id is None:
            recurrence_rules = getattr(google_event, "recurrence", None)
            if recurrence_rules:
                series_platform_id = google_event.id

        calendar_entry_series_id = (
            CalendarEntrySeriesEntity.id_from_platform("google", series_platform_id)
            if series_platform_id
            else None
        )

        return CalendarEntryEntity(
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
            calendar_entry_series_id=calendar_entry_series_id,
        )
