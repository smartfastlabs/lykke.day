"""AuditLog entity for tracking user activities."""

from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lykke.core.exceptions import DomainError

from .base import BaseEntityObject


def _get_user_timezone_date(timezone: str | None = None) -> dt_date:
    """Get the current date in the user's timezone (UTC fallback)."""
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            return datetime.now(UTC).astimezone(tz).date()
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return datetime.now(UTC).date()


@dataclass(kw_only=True)
class AuditLogEntity(BaseEntityObject):
    """Immutable entity representing a user activity audit log entry.

    AuditLog entries are append-only and cannot be updated or deleted once created.
    They track significant user actions for audit, analytics, and context purposes.
    The meta field includes a JSON-serializable snapshot of the entity that
    generated the audit log under the "entity_data" key.

    The activity_type is the name of the domain event that triggered this audit log.
    The date field is the date (in user's timezone) when the activity occurred.
    """

    user_id: UUID
    activity_type: str  # Domain event class name (e.g., "TaskCompletedEvent")
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    date: dt_date = field(default_factory=_get_user_timezone_date)
    entity_id: UUID | None = None
    entity_type: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def delete(self) -> "AuditLogEntity":
        """Prevent deletion of audit log entries.

        Audit logs are immutable and cannot be deleted.

        Raises:
            DomainError: Always raised, as audit logs cannot be deleted.
        """
        raise DomainError("Audit log entries cannot be deleted")

    def apply_update(
        self,
        update_object: Any,
        update_event_class: type[Any],
    ) -> "AuditLogEntity":
        """Prevent updates to audit log entries.

        Audit logs are immutable and cannot be updated.

        Args:
            update_object: Ignored
            update_event_class: Ignored

        Raises:
            DomainError: Always raised, as audit logs cannot be updated.
        """
        raise DomainError("Audit log entries cannot be updated")
