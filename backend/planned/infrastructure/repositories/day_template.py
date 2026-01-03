from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain import entities, value_objects
from planned.infrastructure.database.tables import day_templates_tbl

from .base import DayTemplateQuery, UserScopedBaseRepository


class DayTemplateRepository(UserScopedBaseRepository[entities.DayTemplate, DayTemplateQuery]):
    Object = entities.DayTemplate
    table = day_templates_tbl
    QueryClass = DayTemplateQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize DayTemplateRepository with user scoping."""
        super().__init__(user_id=user_id)

    def build_query(self, query: DayTemplateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.slug is not None:
            stmt = stmt.where(self.table.c.slug == query.slug)

        return stmt

    @staticmethod
    def entity_to_row(template: entities.DayTemplate) -> dict[str, Any]:
        """Convert a DayTemplate entity to a database row dict."""
        row: dict[str, Any] = {
            "id": template.id,
            "user_id": template.user_id,
            "slug": template.slug,
            "icon": template.icon,
        }

        # Handle JSONB fields
        from planned.infrastructure.utils.serialization import dataclass_to_json_dict

        if template.alarm:
            row["alarm"] = dataclass_to_json_dict(template.alarm)
        
        # Handle list fields - convert UUIDs to strings for JSON serialization
        if template.routine_ids:
            row["routine_ids"] = [str(routine_id) for routine_id in template.routine_ids]
        else:
            row["routine_ids"] = []

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> entities.DayTemplate:
        """Convert a database row dict to a DayTemplate entity.

        Overrides base to handle UUID conversion for routine_ids stored as JSON strings.
        """
        from planned.infrastructure.repositories.base.utils import normalize_list_fields

        data = normalize_list_fields(dict(row), entities.DayTemplate)

        # Convert string UUIDs back to UUID objects for routine_ids
        if "routine_ids" in data and data["routine_ids"]:
            data["routine_ids"] = [
                UUID(routine_id) if isinstance(routine_id, str) else routine_id
                for routine_id in data["routine_ids"]
            ]
        
        # Handle alarm - it comes as a dict from JSONB, need to convert to value object
        if "alarm" in data and data["alarm"]:
            if isinstance(data["alarm"], dict):
                alarm_data = dict(data["alarm"])
                # Convert time string back to time object if needed
                if "time" in alarm_data and isinstance(alarm_data["time"], str):
                    from datetime import time as dt_time
                    alarm_data["time"] = dt_time.fromisoformat(alarm_data["time"])
                # Convert type string to enum if needed
                if "type" in alarm_data and isinstance(alarm_data["type"], str):
                    alarm_data["type"] = value_objects.AlarmType(alarm_data["type"])
                # Convert triggered_at string to time object if needed
                if "triggered_at" in alarm_data and alarm_data["triggered_at"] and isinstance(alarm_data["triggered_at"], str):
                    from datetime import time as dt_time
                    alarm_data["triggered_at"] = dt_time.fromisoformat(alarm_data["triggered_at"])
                data["alarm"] = value_objects.Alarm(**alarm_data)

        return entities.DayTemplate(**data)

    async def get_by_slug(self, slug: str) -> entities.DayTemplate:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        return await self.get_one(DayTemplateQuery(slug=slug))
