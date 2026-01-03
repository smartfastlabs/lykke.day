from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import ActionEntity, CalendarEntryEntity

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import calendar_entries_tbl


class CalendarEntryRepository(UserScopedBaseRepository[CalendarEntryEntity, DateQuery]):
    Object = CalendarEntryEntity
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
    def entity_to_row(calendar_entry: CalendarEntryEntity) -> dict[str, Any]:
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
        from planned.core.utils.serialization import dataclass_to_json_dict

        if calendar_entry.actions:
            row["actions"] = [
                dataclass_to_json_dict(action) for action in calendar_entry.actions
            ]

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> CalendarEntryEntity:
        """Convert a database row dict to a CalendarEntry entity.
        
        Overrides base to handle enum conversion for frequency field.
        """
        from planned.infrastructure.repositories.base.utils import normalize_list_fields
        from planned.domain import value_objects

        data = normalize_list_fields(dict(row), CalendarEntryEntity)
        
        # Remove 'date' field - it's a computed property, not a constructor argument
        data.pop("date", None)
        
        # Convert frequency string back to enum if needed
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = value_objects.TaskFrequency(data["frequency"])
        
        # Handle actions - they come as dicts from JSONB, need to convert to entities
        if "actions" in data and data["actions"]:
            data["actions"] = [
                ActionEntity(**action) if isinstance(action, dict) else action
                for action in data["actions"]
            ]

        return CalendarEntryEntity(**data)

