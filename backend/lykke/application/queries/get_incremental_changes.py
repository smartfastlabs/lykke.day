"""Query handler to get incremental changes since a timestamp."""

from datetime import date as dt_date, datetime
from typing import Any, Literal
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.core.utils.audit_log_filtering import is_audit_log_for_today
from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity
from lykke.presentation.api.schemas.websocket_message import EntityChangeSchema


class GetIncrementalChangesHandler(BaseQueryHandler):
    """Gets incremental changes since a timestamp, filtered to entities for a specific date."""

    def __init__(self, ro_repos: Any, user_id: UUID) -> None:
        """Initialize the handler with read-only repositories."""
        super().__init__(ro_repos, user_id)
        # Access audit_log_ro_repo from ro_repos (not exposed by BaseQueryHandler)
        self.audit_log_ro_repo = ro_repos.audit_log_ro_repo

    async def get_incremental_changes(
        self, since_timestamp: datetime, target_date: dt_date
    ) -> tuple[list[EntityChangeSchema], datetime | None]:
        """Get incremental changes since a timestamp, filtered to target date.

        Args:
            since_timestamp: Only return changes after this timestamp
            target_date: Only include entities associated with this date

        Returns:
            Tuple of (list of changes, last_audit_log_timestamp)
        """
        # Query audit logs since timestamp
        query = value_objects.AuditLogQuery(occurred_after=since_timestamp)
        audit_logs = await self.audit_log_ro_repo.search(query)

        # Filter to only include entities for target_date
        filtered_logs: list[AuditLogEntity] = []
        for audit_log in audit_logs:
            if await is_audit_log_for_today(audit_log, target_date):
                filtered_logs.append(audit_log)

        # Sort by occurred_at to process in order
        filtered_logs.sort(key=lambda x: x.occurred_at)

        # Build changes from filtered audit logs
        changes: list[EntityChangeSchema] = []
        last_timestamp: datetime | None = None

        for audit_log in filtered_logs:
            # Determine change type from activity_type
            change_type: Literal["created", "updated", "deleted"] | None = None
            if (
                "Created" in audit_log.activity_type
                or audit_log.activity_type == "EntityCreatedEvent"
            ):
                change_type = "created"
            elif (
                "Deleted" in audit_log.activity_type
                or audit_log.activity_type == "EntityDeletedEvent"
            ):
                change_type = "deleted"
            elif (
                "Updated" in audit_log.activity_type
                or audit_log.activity_type == "EntityUpdatedEvent"
                or audit_log.activity_type == "TaskCompletedEvent"
                or audit_log.activity_type == "TaskPuntedEvent"
            ):
                change_type = "updated"
            else:
                # Skip events we don't know how to handle
                continue

            entity_data: dict[str, Any] | None = None

            # For created/updated, load the entity and include its data
            if change_type in ("created", "updated"):
                entity_data = _get_audit_log_entity_data(audit_log)

            change = EntityChangeSchema(
                change_type=change_type,
                entity_type=audit_log.entity_type or "unknown",
                entity_id=audit_log.entity_id
                or UUID("00000000-0000-0000-0000-000000000000"),
                entity_data=entity_data,
            )
            changes.append(change)

            # Track the latest timestamp
            if not last_timestamp or audit_log.occurred_at > last_timestamp:
                last_timestamp = audit_log.occurred_at

        # If no changes, get the most recent audit log timestamp anyway
        if not last_timestamp:
            all_logs = await self.audit_log_ro_repo.search(
                value_objects.AuditLogQuery()
            )
            if all_logs:
                sorted_logs = sorted(
                    all_logs, key=lambda x: x.occurred_at, reverse=True
                )
                last_timestamp = sorted_logs[0].occurred_at

        return changes, last_timestamp


def _get_audit_log_entity_data(audit_log: AuditLogEntity) -> dict[str, Any] | None:
    return audit_log.meta.get("entity_data", None)
