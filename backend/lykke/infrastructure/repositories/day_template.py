from datetime import time as dt_time
from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.infrastructure.database.tables import day_templates_tbl
from lykke.infrastructure.repositories.base.utils import (
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import DayTemplateQuery, UserScopedBaseRepository


class DayTemplateRepository(
    UserScopedBaseRepository[DayTemplateEntity, DayTemplateQuery]
):
    Object = DayTemplateEntity
    table = day_templates_tbl
    QueryClass = DayTemplateQuery

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
            "start_time": template.start_time,
            "end_time": template.end_time,
            "icon": template.icon,
        }

        # Handle JSONB fields
        from lykke.core.utils.serialization import dataclass_to_json_dict

        # Always include high_level_plan, even if None, so that clearing it works
        row["high_level_plan"] = (
            dataclass_to_json_dict(template.high_level_plan)
            if template.high_level_plan
            else None
        )

        # Handle list fields - convert UUIDs to strings for JSON serialization
        if template.routine_definition_ids:
            row["routine_definition_ids"] = [
                str(routine_definition_id)
                for routine_definition_id in template.routine_definition_ids
            ]
        else:
            row["routine_definition_ids"] = []

        # Handle time_blocks - serialize to JSON
        if template.time_blocks:
            row["time_blocks"] = [
                {
                    "time_block_definition_id": str(tb.time_block_definition_id),
                    "start_time": tb.start_time.isoformat(),
                    "end_time": tb.end_time.isoformat(),
                    "name": tb.name,
                }
                for tb in template.time_blocks
            ]
        else:
            row["time_blocks"] = []

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> DayTemplateEntity:
        """Convert a database row dict to a DayTemplate entity.

        Overrides base to handle UUID conversion for routine_definition_ids stored as JSON strings.
        """
        data = normalize_list_fields(dict(row), DayTemplateEntity)

        # Filter out fields with init=False (e.g., _domain_events)
        data = filter_init_false_fields(data, DayTemplateEntity)

        # Backward compatibility: rename routine_ids -> routine_definition_ids
        if "routine_ids" in data and "routine_definition_ids" not in data:
            data["routine_definition_ids"] = data.pop("routine_ids")
        else:
            data.pop("routine_ids", None)

        # Convert string UUIDs back to UUID objects for routine_definition_ids
        if data.get("routine_definition_ids"):
            data["routine_definition_ids"] = [
                UUID(routine_definition_id)
                if isinstance(routine_definition_id, str)
                else routine_definition_id
                for routine_definition_id in data["routine_definition_ids"]
            ]

        # Handle high_level_plan - it comes as a dict from JSONB
        if data.get("high_level_plan") and isinstance(data["high_level_plan"], dict):
            plan_data = data["high_level_plan"]
            data["high_level_plan"] = value_objects.HighLevelPlan(
                title=plan_data.get("title"),
                text=plan_data.get("text"),
                intentions=plan_data.get("intentions") or [],
            )

        # Handle time_blocks - deserialize from JSON
        if data.get("time_blocks"):
            data["time_blocks"] = [
                value_objects.DayTemplateTimeBlock(
                    time_block_definition_id=(
                        UUID(tb["time_block_definition_id"])
                        if isinstance(tb["time_block_definition_id"], str)
                        else tb["time_block_definition_id"]
                    ),
                    start_time=(
                        dt_time.fromisoformat(tb["start_time"])
                        if isinstance(tb["start_time"], str)
                        else tb["start_time"]
                    ),
                    end_time=(
                        dt_time.fromisoformat(tb["end_time"])
                        if isinstance(tb["end_time"], str)
                        else tb["end_time"]
                    ),
                    name=tb["name"],
                )
                for tb in data["time_blocks"]
            ]

        return DayTemplateEntity(**data)
