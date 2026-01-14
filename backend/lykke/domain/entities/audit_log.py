"""AuditLog entity for tracking user activities."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lykke.core.exceptions import DomainError
from lykke.domain.value_objects.activity_type import ActivityType

from .base import BaseEntityObject


@dataclass(kw_only=True)
class AuditLogEntity(BaseEntityObject):
    """Immutable entity representing a user activity audit log entry.

    AuditLog entries are append-only and cannot be updated or deleted once created.
    They track significant user actions for audit, analytics, and context purposes.
    """

    user_id: UUID
    activity_type: ActivityType
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
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
