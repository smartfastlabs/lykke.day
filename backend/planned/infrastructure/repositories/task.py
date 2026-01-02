from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain import entities

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import tasks_tbl


class TaskRepository(UserScopedBaseRepository[entities.Task, DateQuery]):
    Object = entities.Task
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
    def entity_to_row(task: entities.Task) -> dict[str, Any]:
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
        row["task_definition"] = task.task_definition.model_dump(mode="json")

        if task.schedule:
            row["schedule"] = task.schedule.model_dump(mode="json")

        if task.tags:
            row["tags"] = [tag.value for tag in task.tags]

        if task.actions:
            row["actions"] = [action.model_dump(mode="json") for action in task.actions]

        return row
