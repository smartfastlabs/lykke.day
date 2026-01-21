"""Query handler to get incremental changes since a timestamp."""

from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import Any, Literal
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.utils.audit_log_filtering import is_audit_log_for_today
from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity
from lykke.presentation.api.schemas.websocket_message import EntityChangeSchema


@dataclass(frozen=True)
class GetIncrementalChangesQuery(Query):
    """Query to get incremental changes."""

    since: datetime
    date: dt_date


class GetIncrementalChangesHandler(BaseQueryHandler[GetIncrementalChangesQuery, tuple[list[EntityChangeSchema], datetime | None]]):
    """Gets incremental changes since a timestamp, filtered to entities for a specific date."""

    def __init__(self, ro_repos: Any, user_id: UUID) -> None:
        """Initialize the handler with read-only repositories."""
        super().__init__(ro_repos, user_id)
        # Access audit_log_ro_repo from ro_repos (not exposed by BaseQueryHandler)
        self.audit_log_ro_repo = ro_repos.audit_log_ro_repo
        self.task_ro_repo = ro_repos.task_ro_repo
        self.calendar_entry_ro_repo = ro_repos.calendar_entry_ro_repo
        self.routine_ro_repo = ro_repos.routine_ro_repo
        self.day_ro_repo = ro_repos.day_ro_repo

    async def handle(self, query: GetIncrementalChangesQuery) -> tuple[list[EntityChangeSchema], datetime | None]:
        """Handle get incremental changes query."""
        return await self.get_incremental_changes(query.since, query.date)

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

        user_timezone = None
        try:
            user = await self.user_ro_repo.get(self.user_id)
            user_timezone = user.settings.timezone if user.settings else None
        except Exception:
            user_timezone = None

        # Filter to only include entities for target_date
        filtered_logs: list[AuditLogEntity] = []
        for audit_log in audit_logs:
            if await is_audit_log_for_today(
                audit_log, target_date, user_timezone=user_timezone
            ):
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
                or audit_log.activity_type == "BrainDumpItemAddedEvent"
                or audit_log.activity_type == "BrainDumpItemStatusChangedEvent"
                or audit_log.activity_type == "BrainDumpItemRemovedEvent"
            ):
                change_type = "updated"
            else:
                # Skip events we don't know how to handle
                continue

            entity_data: dict[str, Any] | None = None

            # For created/updated, load the full entity from the database
            if change_type in ("created", "updated") and audit_log.entity_id:
                entity_data = await self._load_entity_data(
                    audit_log.entity_type or "unknown",
                    audit_log.entity_id,
                    user_timezone=user_timezone,
                )

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
            # Use limit=1 with descending order to fetch only the most recent record
            # This avoids loading all audit logs into memory
            recent_logs = await self.audit_log_ro_repo.search(
                value_objects.AuditLogQuery(
                    limit=1, order_by="occurred_at", order_by_desc=True
                )
            )
            if recent_logs:
                last_timestamp = recent_logs[0].occurred_at

        return changes, last_timestamp

    async def _load_entity_data(
        self,
        entity_type: str,
        entity_id: UUID,
        *,
        user_timezone: str | None,
    ) -> dict[str, Any] | None:
        """Load the full entity data from the repository and convert to dict.

        Args:
            entity_type: The type of entity (task, calendar_entry, etc.)
            entity_id: The ID of the entity

        Returns:
            Dictionary representation of the entity, or None if not found
        """
        try:
            if entity_type == "task":
                task = await self.task_ro_repo.get(entity_id)
                if not task:
                    return None
                # Convert task entity to dict using schema mapper
                from lykke.presentation.api.schemas.mappers import map_task_to_schema

                task_schema = map_task_to_schema(task)
                return task_schema.model_dump(mode="json")

            elif entity_type == "calendarentry":
                entry = await self.calendar_entry_ro_repo.get(entity_id)
                if not entry:
                    return None
                # Convert calendar entry to dict using schema mapper
                from lykke.presentation.api.schemas.mappers import (
                    map_calendar_entry_to_schema,
                )

                entry_schema = map_calendar_entry_to_schema(
                    entry, user_timezone=user_timezone
                )
                return entry_schema.model_dump(mode="json")

            elif entity_type == "routine":
                routine = await self.routine_ro_repo.get(entity_id)
                if not routine:
                    return None
                # Convert routine to dict using schema mapper
                from lykke.presentation.api.schemas.mappers import (
                    map_routine_to_schema,
                )

                routine_schema = map_routine_to_schema(routine)
                return routine_schema.model_dump(mode="json")

            elif entity_type == "day":
                day = await self.day_ro_repo.get(entity_id)
                if not day:
                    return None
                # Convert day to dict using schema mapper
                from lykke.presentation.api.schemas.mappers import (
                    map_day_to_schema,
                )

                day_schema = map_day_to_schema(day)
                return day_schema.model_dump(mode="json")

            return None
        except Exception:
            # If we can't load the entity, return None
            # The change will still be sent but without entity_data
            return None
