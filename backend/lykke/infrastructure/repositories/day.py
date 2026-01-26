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
            "starts_at": day.starts_at,
            "ends_at": day.ends_at,
        }

        # Handle JSONB fields
        from lykke.core.utils.serialization import dataclass_to_json_dict

        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.template:
            row["template"] = dataclass_to_json_dict(day.template)

        # Always include high_level_plan, even if None, so that clearing it works
        row["high_level_plan"] = (
            dataclass_to_json_dict(day.high_level_plan) if day.high_level_plan else None
        )

        # Always include reminders, even if empty, so that removing all reminders
        # clears the field in the database
        row["reminders"] = (
            [dataclass_to_json_dict(reminder) for reminder in day.reminders]
            if day.reminders
            else []
        )

        # Always include alarms, even if empty, so that removing all alarms
        # clears the field in the database
        row["alarms"] = (
            [dataclass_to_json_dict(alarm) for alarm in day.alarms]
            if day.alarms
            else []
        )

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> DayEntity:
        """Convert a database row dict to a Day entity.

        Overrides base to handle JSONB fields (template) and enum conversion.
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

        # Handle high_level_plan - it comes as a dict from JSONB
        if data.get("high_level_plan") and isinstance(data["high_level_plan"], dict):
            plan_data = data["high_level_plan"]
            data["high_level_plan"] = value_objects.HighLevelPlan(
                title=plan_data.get("title"),
                text=plan_data.get("text"),
                intentions=plan_data.get("intentions") or [],
            )

        # Handle template - it comes as a dict from JSONB, need to convert to entity
        if data.get("template") and isinstance(data["template"], dict):
            template_data = dict(data["template"])
            # Convert string UUIDs to UUID objects (JSONB stores UUIDs as strings)
            if "id" in template_data and isinstance(template_data["id"], str):
                template_data["id"] = UUID(template_data["id"])
            if "user_id" in template_data and isinstance(template_data["user_id"], str):
                template_data["user_id"] = UUID(template_data["user_id"])

            # Backward compatibility: rename routine_ids -> routine_definition_ids
            if (
                "routine_ids" in template_data
                and "routine_definition_ids" not in template_data
            ):
                template_data["routine_definition_ids"] = template_data.pop(
                    "routine_ids"
                )
            else:
                template_data.pop("routine_ids", None)

            # Convert routine_definition_ids from strings to UUIDs
            if template_data.get("routine_definition_ids"):
                template_data["routine_definition_ids"] = [
                    UUID(routine_definition_id)
                    if isinstance(routine_definition_id, str)
                    else routine_definition_id
                    for routine_definition_id in template_data[
                        "routine_definition_ids"
                    ]
                ]

            # Convert start/end times from strings to time objects
            if "start_time" in template_data and isinstance(
                template_data["start_time"], str
            ):
                from datetime import time as dt_time

                template_data["start_time"] = dt_time.fromisoformat(
                    template_data["start_time"]
                )
            if "end_time" in template_data and isinstance(
                template_data["end_time"], str
            ):
                from datetime import time as dt_time

                template_data["end_time"] = dt_time.fromisoformat(
                    template_data["end_time"]
                )

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

            if template_data.get("alarms"):
                template_data["alarms"] = [
                    value_objects.Alarm.from_dict(alarm)
                    for alarm in template_data["alarms"]
                    if isinstance(alarm, dict)
                ]

            if template_data.get("high_level_plan"):
                high_level_plan = template_data.get("high_level_plan")
                if isinstance(high_level_plan, dict):
                    template_data["high_level_plan"] = value_objects.HighLevelPlan(
                        title=high_level_plan.get("title"),
                        text=high_level_plan.get("text"),
                        intentions=high_level_plan.get("intentions") or [],
                    )

            from lykke.infrastructure.repositories.base.utils import (
                filter_init_false_fields,
            )

            template_data = filter_init_false_fields(template_data, DayTemplateEntity)
            data["template"] = DayTemplateEntity(**template_data)

        # Handle reminders - it comes as a list of dicts from JSONB, need to convert to Reminder value objects
        if data.get("reminders") and isinstance(data["reminders"], list):
            from datetime import datetime as dt_datetime

            reminders_list = []
            for reminder_dict in data["reminders"]:
                if isinstance(reminder_dict, dict):
                    reminder_data = dict(reminder_dict)
                    # Convert string UUIDs to UUID objects
                    if "id" in reminder_data and isinstance(reminder_data["id"], str):
                        reminder_data["id"] = UUID(reminder_data["id"])
                    # Convert status string to enum if needed
                    if "status" in reminder_data and isinstance(
                        reminder_data["status"], str
                    ):
                        reminder_data["status"] = value_objects.ReminderStatus(
                            reminder_data["status"]
                        )
                    # Convert created_at string to datetime if needed
                    if (
                        "created_at" in reminder_data
                        and reminder_data["created_at"]
                        and isinstance(reminder_data["created_at"], str)
                    ):
                        reminder_data["created_at"] = dt_datetime.fromisoformat(
                            reminder_data["created_at"].replace("Z", "+00:00")
                        )
                    reminders_list.append(value_objects.Reminder(**reminder_data))
            data["reminders"] = reminders_list

        # Handle alarms - it comes as a list of dicts from JSONB, need to convert to Alarm value objects
        if data.get("alarms") and isinstance(data["alarms"], list):
            data["alarms"] = [
                value_objects.Alarm.from_dict(alarm)
                for alarm in data["alarms"]
                if isinstance(alarm, dict)
            ]

        from lykke.infrastructure.repositories.base.utils import (
            filter_init_false_fields,
        )

        data = filter_init_false_fields(data, DayEntity)
        data = ensure_datetimes_utc(data, keys=("scheduled_at", "starts_at", "ends_at"))
        return DayEntity(**data)
