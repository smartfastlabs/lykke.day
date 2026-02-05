from datetime import UTC
from typing import Any, ClassVar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity
from lykke.infrastructure.database.tables import calendar_entries_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetime_utc,
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import CalendarEntryQuery, UserScopedBaseRepository


class CalendarEntryRepository(
    UserScopedBaseRepository[CalendarEntryEntity, CalendarEntryQuery]
):
    Object = CalendarEntryEntity
    table = calendar_entries_tbl
    QueryClass = CalendarEntryQuery
    # Exclude 'date' - it's a database-only field for querying (computed from starts_at)
    excluded_row_fields: ClassVar[set[str]] = {"date"}

    def build_query(self, query: CalendarEntryQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.calendar_id is not None:
            stmt = stmt.where(self.table.c.calendar_id == query.calendar_id)

        if query.calendar_entry_series_id is not None:
            stmt = stmt.where(
                self.table.c.calendar_entry_series_id
                == query.calendar_entry_series_id
            )

        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        if query.platform_id is not None:
            stmt = stmt.where(self.table.c.platform_id == query.platform_id)

        if query.platform_ids:
            stmt = stmt.where(self.table.c.platform_id.in_(query.platform_ids))

        if query.ical_uid is not None:
            stmt = stmt.where(self.table.c.ical_uid == query.ical_uid)

        if query.recurring_platform_id is not None:
            stmt = stmt.where(
                self.table.c.recurring_platform_id == query.recurring_platform_id
            )

        if query.starts_at_after is not None:
            stmt = stmt.where(self.table.c.starts_at >= query.starts_at_after)

        return stmt

    @staticmethod
    def entity_to_row(calendar_entry: CalendarEntryEntity) -> dict[str, Any]:
        """Convert a CalendarEntry entity to a database row dict."""
        starts_at_utc = ensure_datetime_utc(calendar_entry.starts_at)
        ends_at_utc = ensure_datetime_utc(calendar_entry.ends_at)
        created_at_utc = ensure_datetime_utc(calendar_entry.created_at)
        updated_at_utc = ensure_datetime_utc(calendar_entry.updated_at)
        user_timezone = calendar_entry.user_timezone or calendar_entry.timezone
        if starts_at_utc is None:
            raise ValueError("CalendarEntry starts_at is required")
        try:
            tz = ZoneInfo(user_timezone) if user_timezone else UTC
        except (ZoneInfoNotFoundError, ValueError):
            tz = UTC
        date_for_user = starts_at_utc.astimezone(tz).date()

        row: dict[str, Any] = {
            "id": calendar_entry.id,
            "user_id": calendar_entry.user_id,
            "date": date_for_user,
            "name": calendar_entry.name,
            "calendar_id": calendar_entry.calendar_id,
            "calendar_entry_series_id": calendar_entry.calendar_entry_series_id,
            "platform_id": calendar_entry.platform_id,
            "platform": calendar_entry.platform,
            "status": calendar_entry.status,
            "attendance_status": (
                calendar_entry.attendance_status.value
                if calendar_entry.attendance_status is not None
                else None
            ),
            "starts_at": starts_at_utc,
            "frequency": calendar_entry.frequency.value,
            "ends_at": ends_at_utc,
            "created_at": created_at_utc,
            "updated_at": updated_at_utc,
            "ical_uid": calendar_entry.ical_uid,
            "original_starts_at": ensure_datetime_utc(calendar_entry.original_starts_at),
            "recurring_platform_id": calendar_entry.recurring_platform_id,
        }

        # Handle JSONB fields
        if calendar_entry.actions:
            row["actions"] = [
                dataclass_to_json_dict(action) for action in calendar_entry.actions
            ]
        if calendar_entry.category is not None:
            row["category"] = calendar_entry.category.value

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> CalendarEntryEntity:
        """Convert a database row dict to a CalendarEntry entity.

        Overrides base to handle enum conversion for frequency field.
        """
        data = normalize_list_fields(dict(row), CalendarEntryEntity)

        # Remove 'date' field - it's a computed property, not a constructor argument
        data.pop("date", None)
        # Convert frequency string back to enum if needed
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = value_objects.TaskFrequency(data["frequency"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = value_objects.EventCategory(data["category"])
        if "attendance_status" in data and isinstance(data["attendance_status"], str):
            data["attendance_status"] = value_objects.CalendarEntryAttendanceStatus(
                data["attendance_status"]
            )

        # Handle actions - they come as dicts from JSONB, need to convert to value objects
        if data.get("actions"):
            data["actions"] = [
                value_objects.Action(
                    **filter_init_false_fields(action, value_objects.Action)
                )
                if isinstance(action, dict)
                else action
                for action in data["actions"]
            ]

        data = ensure_datetimes_utc(
            data,
            keys=(
                "starts_at",
                "ends_at",
                "created_at",
                "updated_at",
                "original_starts_at",
            ),
        )
        data = filter_init_false_fields(data, CalendarEntryEntity)
        return CalendarEntryEntity(**data)
