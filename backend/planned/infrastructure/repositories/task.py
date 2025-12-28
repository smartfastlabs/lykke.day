from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import Task

from .base import BaseRepository, DateQuery
from .base.schema import tasks
from .base.utils import normalize_list_fields


class TaskRepository(BaseRepository[Task, DateQuery]):
    Object = Task
    table = tasks
    QueryClass = DateQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize TaskRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

    def build_query(self, query: DateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        return stmt

    @staticmethod
    def entity_to_row(task: Task) -> dict[str, Any]:
        """Convert a Task entity to a database row dict."""
        row: dict[str, Any] = {
            "id": task.id,
            "user_uuid": task.user_uuid,
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
        row["task_definition"] = task.task_definition.model_dump(mode="json")

        if task.schedule:
            row["schedule"] = task.schedule.model_dump(mode="json")

        if task.tags:
            row["tags"] = [tag.value for tag in task.tags]

        if task.actions:
            row["actions"] = [action.model_dump(mode="json") for action in task.actions]

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Task:
        """Convert a database row dict to a Task entity."""
        # Remove 'date' field - it's database-only for querying
        # The entity computes date from scheduled_date
        data = {k: v for k, v in row.items() if k != "date"}

        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(data, Task)

        return Task.model_validate(data, from_attributes=True)
