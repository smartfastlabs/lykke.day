from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain import data_objects, value_objects
from planned.domain.entities import TaskEntity

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import tasks_tbl


class TaskRepository(UserScopedBaseRepository[TaskEntity, DateQuery]):
    Object = TaskEntity
    table = tasks_tbl
    QueryClass = DateQuery
    # Exclude 'date' - it's a database-only field for querying (computed from scheduled_date)
    excluded_row_fields = {"date"}

    def __init__(self, user_id: UUID) -> None:
        """Initialize TaskRepository with user scoping."""
        super().__init__(user_id=user_id)

    def build_query(self, query: DateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        return stmt

    @staticmethod
    def entity_to_row(task: TaskEntity) -> dict[str, Any]:
        """Convert a Task entity to a database row dict."""
        row: dict[str, Any] = {
            "id": task.id,
            "user_id": task.user_id,
            "date": task.scheduled_date,  # Extract date from scheduled_date for querying
            "scheduled_date": task.scheduled_date,
            "name": task.name,
            "status": task.status.value,
            "category": task.category.value,
            "frequency": task.frequency.value,
            "completed_at": task.completed_at,
            "routine_id": task.routine_id,
        }

        # Handle JSONB fields - task_definition is required, others are optional
        from planned.core.utils.serialization import dataclass_to_json_dict

        row["task_definition"] = dataclass_to_json_dict(task.task_definition)

        if task.schedule:
            row["schedule"] = dataclass_to_json_dict(task.schedule)

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
        from planned.infrastructure.repositories.base.utils import normalize_list_fields
        from planned.domain import value_objects

        data = normalize_list_fields(dict(row), TaskEntity)
        
        # Remove 'date' field - it's a computed property, not a constructor argument
        data.pop("date", None)
        
        # Convert enum strings back to enums if needed
        if "status" in data and isinstance(data["status"], str):
            data["status"] = value_objects.TaskStatus(data["status"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = value_objects.TaskCategory(data["category"])
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = value_objects.TaskFrequency(data["frequency"])
        
        # Handle JSONB fields - task_definition, schedule, tags, actions
        from planned.infrastructure.repositories.base.utils import filter_init_false_fields
        
        if "task_definition" in data and isinstance(data["task_definition"], dict):
            # TaskDefinition is a dataclass
            task_def_dict = filter_init_false_fields(
                data["task_definition"], data_objects.TaskDefinition
            )
            # Convert enum strings back to enums
            if "type" in task_def_dict and isinstance(task_def_dict["type"], str):
                task_def_dict["type"] = value_objects.TaskType(task_def_dict["type"])
            data["task_definition"] = data_objects.TaskDefinition(**task_def_dict)
        
        if "schedule" in data and data["schedule"] is not None:
            if isinstance(data["schedule"], dict):
                # TaskSchedule is a Pydantic model
                schedule_dict = data["schedule"]
                # Convert enum strings back to enums
                if "timing_type" in schedule_dict and isinstance(schedule_dict["timing_type"], str):
                    schedule_dict["timing_type"] = value_objects.TimingType(schedule_dict["timing_type"])
                # Convert time strings back to time objects if needed
                for time_field in ["available_time", "start_time", "end_time"]:
                    if time_field in schedule_dict and isinstance(schedule_dict[time_field], str):
                        from datetime import datetime as dt
                        schedule_dict[time_field] = dt.fromisoformat(schedule_dict[time_field]).time()
                data["schedule"] = value_objects.TaskSchedule.model_validate(schedule_dict)
        
        if "tags" in data and data["tags"]:
            if isinstance(data["tags"], list) and data["tags"]:
                # Tags are stored as strings, convert to TaskTag enums
                data["tags"] = [value_objects.TaskTag(tag) if isinstance(tag, str) else tag for tag in data["tags"]]
        
        # Handle actions - they come as dicts from JSONB, need to convert to value objects
        if "actions" in data and data["actions"]:
            from planned.infrastructure.repositories.base.utils import filter_init_false_fields
            data["actions"] = [
                value_objects.Action(**filter_init_false_fields(action, value_objects.Action))
                if isinstance(action, dict)
                else action
                for action in data["actions"]
            ]

        from planned.infrastructure.repositories.base.utils import filter_init_false_fields
        data = filter_init_false_fields(data, TaskEntity)
        return TaskEntity(**data)
