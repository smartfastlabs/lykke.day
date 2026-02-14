import uuid
from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from loguru import logger

from lykke.core.exceptions import DomainError
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.events.base import (
    EntityCreatedEvent,
    EntityDeletedEvent,
    EntityUpdatedEvent,
)
from lykke.domain.events.calendar_entry_events import (
    CalendarEntryCreatedEvent,
    CalendarEntryDeletedEvent,
    CalendarEntryUpdatedEvent,
)
from lykke.domain.value_objects.update import CalendarEntryUpdateObject


@dataclass(kw_only=True)
class CalendarEntryEntity(BaseEntityObject):
    user_id: UUID
    name: str
    calendar_id: UUID
    calendar_entry_series_id: UUID | None = None
    platform_id: str
    platform: str
    status: str
    attendance_status: value_objects.CalendarEntryAttendanceStatus | None = None
    starts_at: datetime
    frequency: value_objects.TaskFrequency
    category: value_objects.EventCategory | None = None
    ends_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    actions: list[value_objects.Action] = field(default_factory=list)
    timezone: str | None = field(default=None, repr=False)
    user_timezone: str | None = field(default=None, repr=False)
    # Provider identity for reconciliation and single→series conversion.
    ical_uid: str | None = None
    original_starts_at: datetime | None = None  # from originalStartTime; present = exception instance
    recurring_platform_id: str | None = None  # raw recurringEventId when part of a series
    # Set by gateway when Google event has originalStartTime (modified occurrence).
    # Not persisted; used during sync to classify instance-level vs series-level changes.
    is_instance_exception: bool = field(default=False, repr=False)
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
        logger.debug(f"Checking if calendar entry `{self.name}`:")
        # Exclude cancelled calendar entries
        if self.status == "cancelled":
            logger.debug(f"Calendar entry `{self.name}` is cancelled")
            return False

        # Exclude calendar entries that have already ended
        if self.ends_at and self.ends_at < now:
            logger.debug(f"Calendar entry `{self.name}` has already ended")
            return False

        # Include calendar entries that are ongoing (started but not ended)
        if self.starts_at <= now:
            logger.debug(f"Calendar entry `{self.name}` is ongoing")
            return True

        # Exclude calendar entries that are too far in the future
        # Calendar entry will start within look_ahead window
        if (self.starts_at - now) <= look_ahead:
            logger.debug(f"Calendar entry `{self.name}` is within look_ahead window")
            return True

        logger.debug(
            f"Calendar entry `{self.name}` is not eligible for upcoming now: {now} starts_at: {self.starts_at} look_ahead: {look_ahead} diff: {self.starts_at - now}"
        )
        return False

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

    def create_silently(self) -> "CalendarEntryEntity":
        """Mark this entity as created without calendar entry notifications."""
        super().create()
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

    def delete_silently(self) -> "CalendarEntryEntity":
        """Mark this entity for deletion without calendar entry notifications."""
        super().delete()
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
        effective_starts_at = update_object.starts_at or self.starts_at
        if effective_starts_at.tzinfo is None:
            # Defensive: treat naive datetimes as UTC.
            effective_starts_at = effective_starts_at.replace(tzinfo=UTC)

        if update_object.attendance_status is not None:
            now = datetime.now(UTC)
            new_status = update_object.attendance_status

            # Before the meeting starts: you can mark NOT_GOING, but not MISSED.
            if (
                new_status == value_objects.CalendarEntryAttendanceStatus.MISSED
                and effective_starts_at > now
            ):
                raise DomainError("Cannot mark a meeting as MISSED before it starts")

            # After the meeting has started: you can mark MISSED, but not NOT_GOING.
            if (
                new_status == value_objects.CalendarEntryAttendanceStatus.NOT_GOING
                and effective_starts_at <= now
            ):
                raise DomainError(
                    "Cannot mark a meeting as NOT_GOING after it has started"
                )

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

        updated_entity._add_event(
            EntityUpdatedEvent(update_object=update_object, user_id=self.user_id)
        )
        updated_entity._add_event(update_event)

        return updated_entity

    def apply_calendar_entry_update_silently(
        self, update_object: CalendarEntryUpdateObject
    ) -> "CalendarEntryEntity":
        """Apply updates without emitting CalendarEntryUpdatedEvent."""
        return self.apply_update(update_object, EntityUpdatedEvent)
