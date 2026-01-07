from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects.task import TaskCategory
from lykke.infrastructure.database.tables import routines_tbl
from lykke.infrastructure.repositories.base.utils import filter_init_false_fields

from .base import BaseQuery, UserScopedBaseRepository


class RoutineRepository(UserScopedBaseRepository[RoutineEntity, BaseQuery]):
    Object = RoutineEntity
    table = routines_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize RoutineRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(routine: RoutineEntity) -> dict[str, Any]:
        """Convert a Routine entity to a database row dict.

        This is intentionally strict: we expect Pydantic models for schedule/tasks.
        Anything else is considered a caller error.
        """
        row: dict[str, Any] = {
            "id": routine.id,
            "user_id": routine.user_id,
            "name": routine.name,
            "category": routine.category.value
            if hasattr(routine.category, "value")
            else routine.category,
            "description": routine.description,
        }

        if routine.routine_schedule:
            if not isinstance(routine.routine_schedule, value_objects.RoutineSchedule):
                raise TypeError("routine_schedule must be a RoutineSchedule")
            row["routine_schedule"] = routine.routine_schedule.model_dump(mode="json")

        if routine.tasks:
            if not isinstance(routine.tasks, list):
                raise TypeError("tasks must be a list of RoutineTask")
            task_rows: list[dict[str, Any]] = []
            for task in routine.tasks:
                if not isinstance(task, value_objects.RoutineTask):
                    raise TypeError("tasks must contain RoutineTask instances")
                task_rows.append(task.model_dump(mode="json"))
            row["tasks"] = task_rows

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> RoutineEntity:
        """Convert a database row dict to a Routine entity."""
        data = filter_init_false_fields(dict(row), RoutineEntity)

        category = data.get("category")
        if isinstance(category, str):
            data["category"] = TaskCategory(category)

        routine_schedule = data.get("routine_schedule")
        if routine_schedule:
            data["routine_schedule"] = value_objects.RoutineSchedule(**routine_schedule)

        tasks = data.get("tasks") or []
        data["tasks"] = [value_objects.RoutineTask(**task) for task in tasks]

        return RoutineEntity(**data)
