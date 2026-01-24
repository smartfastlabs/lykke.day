"""Helper functions to filter audit logs by checking if entities are associated with a specific date."""

from datetime import date as dt_date, datetime as dt_datetime
from typing import Any

from lykke.core.utils.dates import resolve_timezone
from lykke.domain.entities import AuditLogEntity


async def is_audit_log_for_today(
    audit_log: AuditLogEntity,
    target_date: dt_date,
    *,
    user_timezone: str | None = None,
) -> bool:
    """Check if an audit log is for an entity associated with the target date.

    Args:
        audit_log: The audit log to check
        target_date: The date to check against (typically today)
    Returns:
        True if the entity is associated with the target date, False otherwise
    """
    if not audit_log.entity_id or not audit_log.entity_type:
        # If no entity info, we can't determine - default to False for safety
        return False

    entity_type = audit_log.entity_type
    entity_data = _get_entity_data(audit_log)
    if not entity_data:
        return False

    if entity_type == "task":
        scheduled_date = _parse_date_value(entity_data.get("scheduled_date"))
        return scheduled_date == target_date

    if entity_type == "calendarentry":
        entry_date = _parse_date_value(entity_data.get("date"))
        if entry_date is not None:
            return entry_date == target_date

        starts_at = _parse_datetime_value(entity_data.get("starts_at"))
        if starts_at is None:
            return False

        resolved_timezone = resolve_timezone(user_timezone)
        return starts_at.astimezone(resolved_timezone).date() == target_date

    if entity_type == "routine_definition":
        # Routine definitions are always relevant - they're not date-specific
        # but are part of DayContext for today view
        return True

    if entity_type == "day":
        # Day entities have a date field - check if it matches target date
        day_date = _parse_date_value(entity_data.get("date"))
        return day_date == target_date

    # For other entity types, we don't filter (they're not part of DayContext)
    # Return False to be safe
    return False


def _get_entity_data(audit_log: AuditLogEntity) -> dict[str, Any] | None:
    return audit_log.meta.get("entity_data", None)


def _parse_date_value(value: Any) -> dt_date | None:
    # Check datetime first since datetime is a subclass of date
    # If we check date first, datetime objects would pass and be returned as-is
    if isinstance(value, dt_datetime):
        return value.date()
    if isinstance(value, dt_date):
        return value
    if isinstance(value, str):
        try:
            return dt_date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _parse_datetime_value(value: Any) -> dt_datetime | None:
    if isinstance(value, dt_datetime):
        return value
    if isinstance(value, str):
        try:
            return dt_datetime.fromisoformat(value)
        except ValueError:
            return None
    return None
