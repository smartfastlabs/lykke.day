from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.infrastructure.database.tables import days_tbl
from lykke.infrastructure.repositories.base.utils import ensure_datetimes_utc

from .base import BaseQuery, UserScopedBaseRepository


class DayRepository(UserScopedBaseRepository[DayEntity, BaseQuery]):
    Object = DayEntity
    table = days_tbl
    QueryClass = BaseQuery

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
        from lykke.core.utils.serialization import dataclass_to_json_dict

        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = dataclass_to_json_dict(day.alarm)

        if day.template:
            row["template"] = dataclass_to_json_dict(day.template)

        if day.goals:
            row["goals"] = [dataclass_to_json_dict(goal) for goal in day.goals]

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> DayEntity:
        """Convert a database row dict to a Day entity.

        Overrides base to handle JSONB fields (template, alarm) and enum conversion.
        """
        from lykke.infrastructure.repositories.base.utils import normalize_list_fields

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
                
                # Convert routine_ids from strings to UUIDs
                if template_data.get("routine_ids"):
                    template_data["routine_ids"] = [
                        UUID(routine_id) if isinstance(routine_id, str) else routine_id
                        for routine_id in template_data["routine_ids"]
                    ]
                
                # Convert time_blocks from dicts to DayTemplateTimeBlock objects
                if template_data.get("time_blocks"):
                    from datetime import time as dt_time
                    
                    template_data["time_blocks"] = [
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
                        for tb in template_data["time_blocks"]
                    ]
                
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
                from lykke.infrastructure.repositories.base.utils import (
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

        # Handle goals - it comes as a list of dicts from JSONB, need to convert to Goal value objects
        if data.get("goals"):
            if isinstance(data["goals"], list):
                from datetime import datetime as dt_datetime

                goals_list = []
                for goal_dict in data["goals"]:
                    if isinstance(goal_dict, dict):
                        goal_data = dict(goal_dict)
                        # Convert string UUIDs to UUID objects
                        if "id" in goal_data and isinstance(goal_data["id"], str):
                            goal_data["id"] = UUID(goal_data["id"])
                        # Convert status string to enum if needed
                        if "status" in goal_data and isinstance(goal_data["status"], str):
                            goal_data["status"] = value_objects.GoalStatus(goal_data["status"])
                        # Convert created_at string to datetime if needed
                        if "created_at" in goal_data and goal_data["created_at"] and isinstance(
                            goal_data["created_at"], str
                        ):
                            goal_data["created_at"] = dt_datetime.fromisoformat(
                                goal_data["created_at"].replace("Z", "+00:00")
                            )
                        goals_list.append(value_objects.Goal(**goal_data))
                data["goals"] = goals_list

        from lykke.infrastructure.repositories.base.utils import (
            filter_init_false_fields,
        )

        data = filter_init_false_fields(data, DayEntity)
        data = ensure_datetimes_utc(data, keys=("scheduled_at",))
        return DayEntity(**data)
