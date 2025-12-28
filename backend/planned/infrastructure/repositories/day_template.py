from typing import Any
from uuid import UUID

from planned.domain.entities import DayTemplate

from .base import BaseQuery, BaseRepository
from .base.schema import day_templates
from .base.utils import normalize_list_fields


class DayTemplateRepository(BaseRepository[DayTemplate, BaseQuery]):
    Object = DayTemplate
    table = day_templates
    QueryClass = BaseQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize DayTemplateRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

    @staticmethod
    def entity_to_row(template: DayTemplate) -> dict[str, Any]:
        """Convert a DayTemplate entity to a database row dict."""
        row: dict[str, Any] = {
            "id": template.id,
            "user_uuid": template.user_uuid,
            "tasks": template.tasks,
            "icon": template.icon,
        }

        # Handle JSONB fields
        if template.alarm:
            row["alarm"] = template.alarm.model_dump(mode="json")

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> DayTemplate:
        """Convert a database row dict to a DayTemplate entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, DayTemplate)
        return DayTemplate.model_validate(data, from_attributes=True)
