from typing import Any
from uuid import UUID

from planned.domain import value_objects
from planned.domain.entities import DayEntity, DayTemplateEntity
from planned.infrastructure.database.tables import days_tbl

from .base import BaseQuery, UserScopedBaseRepository


class DayRepository(UserScopedBaseRepository[DayEntity, BaseQuery]):
    Object = DayEntity
    table = days_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize DayRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(day: DayEntity) -> dict[str, Any]:
        """Convert a Day entity to a database row dict."""
        row: dict[str, Any] = {
            "id": day.id,
            "user_id": day.user_id,
            "date": day.date,
            "status": day.status.value,
            "scheduled_at": day.scheduled_at,
        }

        # Handle JSONB fields
        from planned.core.utils.serialization import dataclass_to_json_dict

        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = dataclass_to_json_dict(day.alarm)

        if day.template:
            row["template"] = dataclass_to_json_dict(day.template)

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> DayEntity:
        """Convert a database row dict to a Day entity.

        Overrides base to handle JSONB fields (template, alarm) and enum conversion.
        """
        from planned.infrastructure.repositories.base.utils import normalize_list_fields

        data = normalize_list_fields(dict(row), DayEntity)

        # Convert status string back to enum if needed
        if "status" in data and isinstance(data["status"], str):
            data["status"] = value_objects.DayStatus(data["status"])

        # Convert tags from strings to enums if needed
        if data.get("tags"):
            data["tags"] = [
                value_objects.DayTag(tag) if isinstance(tag, str) else tag
                for tag in data["tags"]
            ]

        # Handle template - it comes as a dict from JSONB, need to convert to entity
        if data.get("template"):
            if isinstance(data["template"], dict):
                template_data = dict(data["template"])
                # Convert string UUIDs to UUID objects (JSONB stores UUIDs as strings)
                if "id" in template_data and isinstance(template_data["id"], str):
                    template_data["id"] = UUID(template_data["id"])
                if "user_id" in template_data and isinstance(
                    template_data["user_id"], str
                ):
                    template_data["user_id"] = UUID(template_data["user_id"])
                # Convert nested alarm dict to Alarm value object if present
                if template_data.get("alarm"):
                    if isinstance(template_data["alarm"], dict):
                        alarm_data = dict(template_data["alarm"])
                        # Convert time string back to time object if needed
                        if "time" in alarm_data and isinstance(alarm_data["time"], str):
                            from datetime import time as dt_time

                            alarm_data["time"] = dt_time.fromisoformat(
                                alarm_data["time"]
                            )
                        # Convert type string to enum if needed
                        if "type" in alarm_data and isinstance(alarm_data["type"], str):
                            alarm_data["type"] = value_objects.AlarmType(
                                alarm_data["type"]
                            )
                        # Convert triggered_at string to time object if needed
                        if (
                            "triggered_at" in alarm_data
                            and alarm_data["triggered_at"]
                            and isinstance(alarm_data["triggered_at"], str)
                        ):
                            from datetime import time as dt_time

                            alarm_data["triggered_at"] = dt_time.fromisoformat(
                                alarm_data["triggered_at"]
                            )
                        template_data["alarm"] = value_objects.Alarm(**alarm_data)
                from planned.infrastructure.repositories.base.utils import (
                    filter_init_false_fields,
                )

                template_data = filter_init_false_fields(
                    template_data, DayTemplateEntity
                )
                data["template"] = DayTemplateEntity(**template_data)

        # Handle alarm - it comes as a dict from JSONB, need to convert to value object
        if data.get("alarm"):
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
                if (
                    "triggered_at" in alarm_data
                    and alarm_data["triggered_at"]
                    and isinstance(alarm_data["triggered_at"], str)
                ):
                    from datetime import time as dt_time

                    alarm_data["triggered_at"] = dt_time.fromisoformat(
                        alarm_data["triggered_at"]
                    )
                data["alarm"] = value_objects.Alarm(**alarm_data)

        from planned.infrastructure.repositories.base.utils import (
            filter_init_false_fields,
        )

        data = filter_init_false_fields(data, DayEntity)
        return DayEntity(**data)
