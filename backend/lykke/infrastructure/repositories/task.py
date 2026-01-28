# ruff: noqa: I001
from datetime import time as dt_time
from typing import Any, ClassVar

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity
from lykke.infrastructure.database.tables import tasks_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)
from sqlalchemy.sql import Select

from .base import UserScopedBaseRepository


class TaskRepository(UserScopedBaseRepository[TaskEntity, value_objects.TaskQuery]):
    Object = TaskEntity
    table = tasks_tbl
    QueryClass = value_objects.TaskQuery
    # Exclude 'date' - it's a database-only field for querying (computed from scheduled_date)
    excluded_row_fields: ClassVar[set[str]] = {"date"}

    def build_query(self, query: value_objects.TaskQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        if query.ids:
            stmt = stmt.where(self.table.c.id.in_(query.ids))

        if query.routine_definition_ids:
            stmt = stmt.where(
                self.table.c.routine_definition_id.in_(query.routine_definition_ids)
            )

        if query.is_adhoc is True:
            stmt = stmt.where(self.table.c.routine_definition_id.is_(None))
        elif query.is_adhoc is False:
            stmt = stmt.where(self.table.c.routine_definition_id.is_not(None))

        return stmt

    @staticmethod
    def entity_to_row(task: TaskEntity) -> dict[str, Any]:
        """Convert a Task entity to a database row dict."""

        # Helper to safely get enum value (handles both enum and string)
        def get_enum_value(val: Any) -> str | None:
            if val is None:
                return None
            if isinstance(val, str):
                return val
            return str(val.value)

        row: dict[str, Any] = {
            "id": task.id,
            "user_id": task.user_id,
            "date": task.scheduled_date,  # Extract date from scheduled_date for querying
            "scheduled_date": task.scheduled_date,
            "name": task.name,
            "status": get_enum_value(task.status),
            "type": get_enum_value(task.type),
            "description": task.description,
            "category": get_enum_value(task.category),
            "frequency": get_enum_value(task.frequency),
            "completed_at": task.completed_at,
            "snoozed_until": task.snoozed_until,
            "routine_definition_id": task.routine_definition_id,
        }

        # Handle JSONB fields
        if task.time_window:
            row["time_window"] = dataclass_to_json_dict(task.time_window)

        if task.tags:
            row["tags"] = [tag.value for tag in task.tags]

        if task.actions:
            row["actions"] = [dataclass_to_json_dict(action) for action in task.actions]

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> TaskEntity:
        """Convert a database row dict to a Task entity.

        Overrides base to handle enum conversion and Action value objects.
        """
        data = normalize_list_fields(dict(row), TaskEntity)

        # Remove 'date' field - it's a computed property, not a constructor argument
        data.pop("date", None)

        # Convert enum strings back to enums if needed
        if "status" in data and isinstance(data["status"], str):
            data["status"] = value_objects.TaskStatus(data["status"])
        if "type" in data and isinstance(data["type"], str):
            data["type"] = value_objects.TaskType(data["type"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = value_objects.TaskCategory(data["category"])
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = value_objects.TaskFrequency(data["frequency"])

        # Handle JSONB fields - time_window, tags, actions

        if isinstance(data.get("time_window"), dict):
            # TimeWindow value object
            time_window_dict = data["time_window"]
            # Convert time strings back to time objects if needed
            for time_field in [
                "available_time",
                "start_time",
                "end_time",
                "cutoff_time",
            ]:
                if time_field in time_window_dict and isinstance(
                    time_window_dict[time_field], str
                ):
                    time_window_dict[time_field] = dt_time.fromisoformat(
                        time_window_dict[time_field]
                    )
            data["time_window"] = value_objects.TimeWindow(**time_window_dict)

        if data.get("tags") and isinstance(data["tags"], list):
            # Tags are stored as strings, convert to TaskTag enums
            data["tags"] = [
                value_objects.TaskTag(tag) if isinstance(tag, str) else tag
                for tag in data["tags"]
            ]

        # Handle actions - they come as dicts from JSONB, need to convert to value objects
        if data.get("actions"):
            data["actions"] = [
                value_objects.Action(
                    **filter_init_false_fields(action, value_objects.Action)
                )
                if isinstance(action, dict)
                else action
                for action in data["actions"]
            ]

        data = filter_init_false_fields(data, TaskEntity)
        data = ensure_datetimes_utc(data, keys=("completed_at", "snoozed_until"))
        return TaskEntity(**data)
