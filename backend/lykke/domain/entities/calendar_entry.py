import uuid
from dataclasses import dataclass, field
from datetime import UTC
from datetime import date as dt_date
from datetime import datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from gcsa.event import Event as GoogleEvent
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.entities.calendar_entry_series import CalendarEntrySeriesEntity
from lykke.domain.events.base import EntityCreatedEvent, EntityDeletedEvent
from lykke.domain.events.calendar_entry_events import (
    CalendarEntryCreatedEvent,
    CalendarEntryDeletedEvent,
    CalendarEntryUpdatedEvent,
)
from lykke.domain.value_objects.update import CalendarEntryUpdateObject


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
class CalendarEntryEntity(BaseEntityObject, AuditableEntity):
    user_id: UUID
    name: str
    calendar_id: UUID
    calendar_entry_series_id: UUID | None = None
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
    user_timezone: str | None = field(default=None, repr=False)
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
        timezone_name = self.user_timezone or self.timezone
        try:
            tz = ZoneInfo(timezone_name) if timezone_name else UTC
        except (ZoneInfoNotFoundError, ValueError):
            tz = UTC
        return dt.astimezone(tz).date()

    def is_eligible_for_upcoming(
        self,
        now: datetime,
        look_ahead: timedelta,
    ) -> bool:
        """Check if this calendar entry is eligible to be included in upcoming entries.

        Args:
            now: Current datetime
            look_ahead: The time window to look ahead

        Returns:
            True if the calendar entry should be included, False otherwise
        """
        # Exclude cancelled calendar entries
        if self.status == "cancelled":
            return False

        # Exclude calendar entries that have already ended
        if self.ends_at and self.ends_at < now:
            return False

        # Include calendar entries that are ongoing (started but not ended)
        if self.starts_at <= now:
            return True

        # Exclude calendar entries that are too far in the future
        if (self.starts_at - now) > look_ahead:
            return False

        # Calendar entry will start within look_ahead window
        return True

    def create(self) -> "CalendarEntryEntity":
        """Mark this entity as newly created by adding EntityCreatedEvent and CalendarEntryCreatedEvent.

        Returns:
            Self for method chaining.
        """
        # Call parent to emit EntityCreatedEvent (required for UoW processing)
        super().create()
        # Also emit specific calendar entry event
        self._add_event(
            CalendarEntryCreatedEvent(
                calendar_entry_id=self.id,
                user_id=self.user_id,
            )
        )
        return self

    def delete(self) -> "CalendarEntryEntity":
        """Mark this entity for deletion by adding EntityDeletedEvent and CalendarEntryDeletedEvent.

        Returns:
            Self for method chaining.
        """
        # Call parent to emit EntityDeletedEvent (required for UoW processing)
        super().delete()
        # Build entry snapshot for notification payloads
        entry_dict = dataclass_to_json_dict(self)
        entry_snapshot = {k: v for k, v in entry_dict.items() if not k.startswith("_")}
        # Also emit specific calendar entry event with snapshot
        self._add_event(
            CalendarEntryDeletedEvent(
                calendar_entry_id=self.id,
                user_id=self.user_id,
                entry_snapshot=entry_snapshot,
            )
        )
        return self

    def apply_calendar_entry_update(
        self, update_object: CalendarEntryUpdateObject
    ) -> "CalendarEntryEntity":
        """Apply updates from a CalendarEntryUpdateObject and emit CalendarEntryUpdatedEvent.

        This is a convenience method that uses apply_update with CalendarEntryUpdatedEvent,
        ensuring the event includes user_id and calendar_entry_id.

        Args:
            update_object: The update object containing optional fields to update

        Returns:
            A new instance of the entity with updates applied
        """
        # Apply updates using base method, but we need to create the event manually
        # to include calendar_entry_id and user_id
        from typing import Any

        update_dict: dict[str, Any] = {
            k: v for k, v in update_object.__dict__.items() if v is not None
        }

        # Apply updates using clone
        updated_entity = self.clone(**update_dict)
        # Automatically refresh updated_at if present on entity
        if hasattr(updated_entity, "updated_at"):
            updated_entity = updated_entity.clone(updated_at=datetime.now(UTC))

        # Create the update event with all required fields
        update_event = CalendarEntryUpdatedEvent(
            update_object=update_object,
            calendar_entry_id=self.id,
            user_id=self.user_id,
        )

        # Add both the base EntityUpdatedEvent (for UoW) and our specific event
        from lykke.domain.events.base import EntityUpdatedEvent

        updated_entity._add_event(EntityUpdatedEvent(update_object=update_object))
        updated_entity._add_event(update_event)

        return updated_entity

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
            calendar_entry_series_id=calendar_entry_series_id,
        )
        return calendar_entry
