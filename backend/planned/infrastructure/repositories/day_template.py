from typing import Any

from planned.domain.entities import DayTemplate

from .base import BaseConfigRepository
from .base.schema import day_templates


class DayTemplateRepository(BaseConfigRepository[DayTemplate]):
    Object = DayTemplate
    table = day_templates

    @staticmethod
    def entity_to_row(template: DayTemplate) -> dict[str, Any]:
        """Convert a DayTemplate entity to a database row dict."""
        row: dict[str, Any] = {
            "id": template.id,
            "tasks": template.tasks,
            "icon": template.icon,
        }

        # Handle JSONB fields
        if template.alarm:
            row["alarm"] = template.alarm.model_dump()

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> DayTemplate:
        """Convert a database row dict to a DayTemplate entity."""
        return DayTemplate.model_validate(row, from_attributes=True)
