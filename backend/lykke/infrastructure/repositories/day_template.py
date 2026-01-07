from datetime import time as dt_time
from typing import Any
from uuid import UUID

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.infrastructure.database.tables import day_templates_tbl
from lykke.infrastructure.repositories.base.utils import (
    filter_init_false_fields,
    normalize_list_fields,
)
from sqlalchemy.sql import Select

from .base import DayTemplateQuery, UserScopedBaseRepository


class DayTemplateRepository(
    UserScopedBaseRepository[DayTemplateEntity, DayTemplateQuery]
):
    Object = DayTemplateEntity
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
    def entity_to_row(template: DayTemplateEntity) -> dict[str, Any]:
        """Convert a DayTemplate entity to a database row dict."""
        row: dict[str, Any] = {
            "id": template.id,
            "user_id": template.user_id,
            "slug": template.slug,
            "icon": template.icon,
        }

        # Handle JSONB fields
        if template.alarm:
            row["alarm"] = dataclass_to_json_dict(template.alarm)

        # Handle list fields - convert UUIDs to strings for JSON serialization
        if template.routine_ids:
            row["routine_ids"] = [
                str(routine_id) for routine_id in template.routine_ids
            ]
        else:
            row["routine_ids"] = []

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> DayTemplateEntity:
        """Convert a database row dict to a DayTemplate entity.

        Overrides base to handle UUID conversion for routine_ids stored as JSON strings.
        """
        data = normalize_list_fields(dict(row), DayTemplateEntity)

        # Filter out fields with init=False (e.g., _domain_events)
        data = filter_init_false_fields(data, DayTemplateEntity)

        # Convert string UUIDs back to UUID objects for routine_ids
        if data.get("routine_ids"):
            data["routine_ids"] = [
                UUID(routine_id) if isinstance(routine_id, str) else routine_id
                for routine_id in data["routine_ids"]
            ]

        # Handle alarm - it comes as a dict from JSONB, need to convert to value object
        if data.get("alarm"):
            if isinstance(data["alarm"], dict):
                alarm_data = dict(data["alarm"])
                # Convert time string back to time object if needed
                if "time" in alarm_data and isinstance(alarm_data["time"], str):
                    alarm_data["time"] = dt_time.fromisoformat(alarm_data["time"])
                # Convert type string to enum if needed
                if "type" in alarm_data and isinstance(alarm_data["type"], str):
                    alarm_data["type"] = value_objects.AlarmType(alarm_data["type"])
                # Convert triggered_at string to time object if needed
                if (
                    "triggered_at" in alarm_data
                    and alarm_data["triggered_at"]
                    and isinstance(alarm_data["triggered_at"], str)
                ):
                    alarm_data["triggered_at"] = dt_time.fromisoformat(
                        alarm_data["triggered_at"]
                    )
                data["alarm"] = value_objects.Alarm(**alarm_data)

        return DayTemplateEntity(**data)

