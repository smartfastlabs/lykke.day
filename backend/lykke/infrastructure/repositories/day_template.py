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

        # Handle list fields - convert UUIDs to strings for JSON serialization
        if template.routine_ids:
            row["routine_ids"] = [
                str(routine_id) for routine_id in template.routine_ids
            ]
        else:
            row["routine_ids"] = []

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

