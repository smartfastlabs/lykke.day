"""Helper functions to filter audit logs by checking if entities are associated with a specific date."""

from datetime import date as dt_date
from uuid import UUID

from lykke.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import AuditLogEntity


async def is_audit_log_for_today(
    audit_log: AuditLogEntity,
    target_date: dt_date,
    task_repo: TaskRepositoryReadOnlyProtocol,
    calendar_entry_repo: CalendarEntryRepositoryReadOnlyProtocol,
) -> bool:
    """Check if an audit log is for an entity associated with the target date.

    Args:
        audit_log: The audit log to check
        target_date: The date to check against (typically today)
        task_repo: Repository for loading tasks
        calendar_entry_repo: Repository for loading calendar entries

    Returns:
        True if the entity is associated with the target date, False otherwise
    """
    if not audit_log.entity_id or not audit_log.entity_type:
        # If no entity info, we can't determine - default to False for safety
        return False

    entity_id = audit_log.entity_id
    entity_type = audit_log.entity_type

    if entity_type == "task":
        try:
            task = await task_repo.get(entity_id)
            return task.scheduled_date == target_date
        except NotFoundError:
            # Task doesn't exist - not for today
            return False

    elif entity_type == "calendar_entry":
        try:
            calendar_entry = await calendar_entry_repo.get(entity_id)
            # Use the date property which converts to user's timezone
            return calendar_entry.date == target_date
        except NotFoundError:
            # Calendar entry doesn't exist - not for today
            return False

    # For other entity types, we don't filter (they're not part of DayContext)
    # Return False to be safe
    return False
