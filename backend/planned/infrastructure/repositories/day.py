from typing import Any
from uuid import UUID

from planned.domain import entities

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import days_tbl


class DayRepository(UserScopedBaseRepository[entities.Day, BaseQuery]):
    Object = entities.Day
    table = days_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize DayRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(day: entities.Day) -> dict[str, Any]:
        """Convert a Day entity to a database row dict."""
        row: dict[str, Any] = {
            "id": day.id,
            "user_id": day.user_id,
            "date": day.date,
            "status": day.status.value,
            "scheduled_at": day.scheduled_at,
        }

        # Handle JSONB fields
        from planned.infrastructure.utils.serialization import dataclass_to_json_dict

        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = dataclass_to_json_dict(day.alarm)

        if day.template:
            row["template"] = dataclass_to_json_dict(day.template)

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> entities.Day:
        """Convert a database row dict to a Day entity.
        
        Overrides base to handle JSONB fields (template, alarm) and enum conversion.
        """
        from planned.infrastructure.repositories.base.utils import normalize_list_fields
        from planned.domain import value_objects

        data = normalize_list_fields(dict(row), entities.Day)
        
        # Convert status string back to enum if needed
        if "status" in data and isinstance(data["status"], str):
            data["status"] = value_objects.DayStatus(data["status"])
        
        # Convert tags from strings to enums if needed
        if "tags" in data and data["tags"]:
            data["tags"] = [
                value_objects.DayTag(tag) if isinstance(tag, str) else tag
                for tag in data["tags"]
            ]
        
        # Handle template - it comes as a dict from JSONB, need to convert to entity
        if "template" in data and data["template"]:
            if isinstance(data["template"], dict):
                template_data = dict(data["template"])
                # Convert string UUIDs to UUID objects (JSONB stores UUIDs as strings)
                if "id" in template_data and isinstance(template_data["id"], str):
                    template_data["id"] = UUID(template_data["id"])
                if "user_id" in template_data and isinstance(template_data["user_id"], str):
                    template_data["user_id"] = UUID(template_data["user_id"])
                # Convert nested alarm dict to Alarm entity if present
                if "alarm" in template_data and template_data["alarm"]:
                    if isinstance(template_data["alarm"], dict):
                        template_data["alarm"] = entities.Alarm(**template_data["alarm"])
                data["template"] = entities.DayTemplate(**template_data)
        
        # Handle alarm - it comes as a dict from JSONB, need to convert to entity
        if "alarm" in data and data["alarm"]:
            if isinstance(data["alarm"], dict):
                data["alarm"] = entities.Alarm(**data["alarm"])

        return entities.Day(**data)
