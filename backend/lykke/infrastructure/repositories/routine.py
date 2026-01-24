from dataclasses import asdict
from datetime import datetime, time
from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.value_objects.task import TaskCategory
from lykke.infrastructure.database.tables import routine_definitions_tbl
from lykke.infrastructure.repositories.base.utils import filter_init_false_fields

from .base import BaseQuery, UserScopedBaseRepository


def dataclass_to_json_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict, handling UUIDs, enums, datetime, and time."""
    result = asdict(obj)

    def convert_value(value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, (datetime, time)):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(item) for item in value]
        elif hasattr(value, "value"):  # Enum
            return value.value
        return value

    return {k: convert_value(v) for k, v in result.items()}


class RoutineDefinitionRepository(
    UserScopedBaseRepository[RoutineDefinitionEntity, BaseQuery]
):
    Object = RoutineDefinitionEntity
    table = routine_definitions_tbl
    QueryClass = BaseQuery

    @staticmethod
    def entity_to_row(routine_definition: RoutineDefinitionEntity) -> dict[str, Any]:
        """Convert a RoutineDefinition entity to a database row dict.

        This is intentionally strict: we expect Pydantic models for schedule/tasks.
        Anything else is considered a caller error.
        """
        row: dict[str, Any] = {
            "id": routine_definition.id,
            "user_id": routine_definition.user_id,
            "name": routine_definition.name,
            "category": routine_definition.category.value
            if hasattr(routine_definition.category, "value")
            else routine_definition.category,
            "description": routine_definition.description,
        }

        if routine_definition.routine_definition_schedule:
            if not isinstance(
                routine_definition.routine_definition_schedule,
                value_objects.RecurrenceSchedule,
            ):
                raise TypeError("routine_definition_schedule must be a RecurrenceSchedule")
            row["routine_definition_schedule"] = dataclass_to_json_dict(
                routine_definition.routine_definition_schedule
            )

        if routine_definition.time_window:
            if not isinstance(
                routine_definition.time_window, value_objects.TimeWindow
            ):
                raise TypeError("time_window must be a TimeWindow")
            row["time_window"] = dataclass_to_json_dict(
                routine_definition.time_window
            )

        if routine_definition.tasks:
            if not isinstance(routine_definition.tasks, list):
                raise TypeError("tasks must be a list of RoutineDefinitionTask")
            task_rows: list[dict[str, Any]] = []
            for task in routine_definition.tasks:
                if not isinstance(task, value_objects.RoutineDefinitionTask):
                    raise TypeError(
                        "tasks must contain RoutineDefinitionTask instances"
                    )
                task_rows.append(dataclass_to_json_dict(task))
            row["tasks"] = task_rows

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> RoutineDefinitionEntity:
        """Convert a database row dict to a RoutineDefinition entity."""
        data = filter_init_false_fields(dict(row), RoutineDefinitionEntity)

        category = data.get("category")
        if isinstance(category, str):
            data["category"] = TaskCategory(category)

        routine_definition_schedule = data.get("routine_definition_schedule")
        if routine_definition_schedule:
            data["routine_definition_schedule"] = value_objects.RecurrenceSchedule(
                **routine_definition_schedule
            )

        time_window = data.get("time_window")
        if time_window:
            for time_field in [
                "available_time",
                "start_time",
                "end_time",
                "cutoff_time",
            ]:
                if time_window.get(time_field) and isinstance(
                    time_window[time_field], str
                ):
                    time_window[time_field] = time.fromisoformat(
                        time_window[time_field]
                    )
            data["time_window"] = value_objects.TimeWindow(**time_window)

        tasks = data.get("tasks") or []
        task_objects = []
        for task_dict in tasks:
            # Handle schedule with time fields
            if task_dict.get("schedule"):
                schedule_dict = task_dict["schedule"]
                # Convert time strings to time objects
                for time_field in ["available_time", "start_time", "end_time"]:
                    if schedule_dict.get(time_field) and isinstance(
                        schedule_dict[time_field], str
                    ):
                        schedule_dict[time_field] = time.fromisoformat(
                            schedule_dict[time_field]
                        )
                task_dict["schedule"] = value_objects.TaskSchedule(**schedule_dict)

            # Handle task_schedule (recurrence schedule)
            if task_dict.get("task_schedule"):
                task_dict["task_schedule"] = value_objects.RecurrenceSchedule(
                    **task_dict["task_schedule"]
                )

            # Handle time_window with time fields
            if task_dict.get("time_window"):
                time_window_dict = task_dict["time_window"]
                for time_field in [
                    "available_time",
                    "start_time",
                    "end_time",
                    "cutoff_time",
                ]:
                    if time_window_dict.get(time_field) and isinstance(
                        time_window_dict[time_field], str
                    ):
                        time_window_dict[time_field] = time.fromisoformat(
                            time_window_dict[time_field]
                        )
                task_dict["time_window"] = value_objects.TimeWindow(
                    **time_window_dict
                )

            task_objects.append(value_objects.RoutineDefinitionTask(**task_dict))

        data["tasks"] = task_objects

        return RoutineDefinitionEntity(**data)
