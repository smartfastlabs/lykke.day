from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import DayTemplate
from planned.infrastructure.database.tables import day_templates_tbl

from .base import DayTemplateQuery, UserScopedBaseRepository
from .base.utils import normalize_list_fields


class DayTemplateRepository(UserScopedBaseRepository[DayTemplate, DayTemplateQuery]):
    Object = DayTemplate
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
    def entity_to_row(template: DayTemplate) -> dict[str, Any]:
        """Convert a DayTemplate entity to a database row dict."""
        row: dict[str, Any] = {
            "id": template.id,
            "user_id": template.user_id,
            "slug": template.slug,
            "icon": template.icon,
        }

        # Handle JSONB fields
        if template.alarm:
            row["alarm"] = template.alarm.model_dump(mode="json")
        
        # Handle list fields - convert UUIDs to strings for JSON serialization
        if template.routine_ids:
            row["routine_ids"] = [str(routine_id) for routine_id in template.routine_ids]
        else:
            row["routine_ids"] = []

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> DayTemplate:
        """Convert a database row dict to a DayTemplate entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, DayTemplate)
        
        # Convert string UUIDs back to UUID objects for routine_ids
        if "routine_ids" in data and data["routine_ids"]:
            data["routine_ids"] = [UUID(routine_id) if isinstance(routine_id, str) else routine_id for routine_id in data["routine_ids"]]
        
        return DayTemplate.model_validate(data, from_attributes=True)

    async def get_by_slug(self, slug: str) -> DayTemplate:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        return await self.get_one(DayTemplateQuery(slug=slug))
