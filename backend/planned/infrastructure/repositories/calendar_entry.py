from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain import entities

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import calendar_entries_tbl


class CalendarEntryRepository(UserScopedBaseRepository[entities.CalendarEntry, DateQuery]):
    Object = entities.CalendarEntry
    table = calendar_entries_tbl
    QueryClass = DateQuery
    # Exclude 'date' - it's a database-only field for querying (computed from starts_at)
    excluded_row_fields = {"date"}

    def __init__(self, user_id: UUID) -> None:
        """Initialize CalendarEntryRepository with user scoping."""
        super().__init__(user_id=user_id)

    def build_query(self, query: DateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        return stmt

    @staticmethod
    def entity_to_row(calendar_entry: entities.CalendarEntry) -> dict[str, Any]:
        """Convert a CalendarEntry entity to a database row dict."""
        row: dict[str, Any] = {
            "id": calendar_entry.id,
            "user_id": calendar_entry.user_id,
            "date": calendar_entry.starts_at.date(),  # Extract date from starts_at for querying
            "name": calendar_entry.name,
            "calendar_id": calendar_entry.calendar_id,
            "platform_id": calendar_entry.platform_id,
            "platform": calendar_entry.platform,
            "status": calendar_entry.status,
            "starts_at": calendar_entry.starts_at,
            "frequency": calendar_entry.frequency.value,
            "ends_at": calendar_entry.ends_at,
            "created_at": calendar_entry.created_at,
            "updated_at": calendar_entry.updated_at,
        }

        # Handle JSONB fields
        from planned.infrastructure.utils.serialization import dataclass_to_json_dict

        if calendar_entry.people:
            row["people"] = [dataclass_to_json_dict(person) for person in calendar_entry.people]

        if calendar_entry.actions:
            row["actions"] = [
                dataclass_to_json_dict(action) for action in calendar_entry.actions
            ]

        return row

