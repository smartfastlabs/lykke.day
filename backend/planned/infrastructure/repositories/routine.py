from typing import Any
from uuid import UUID

from planned.domain.entities.routine import Routine

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import routines_tbl


class RoutineRepository(UserScopedBaseRepository[Routine, BaseQuery]):
    Object = Routine
    table = routines_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize RoutineRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(routine: Routine) -> dict[str, Any]:
        """Convert a Routine entity to a database row dict."""
        row: dict[str, Any] = {
            "id": routine.id,
            "user_id": routine.user_id,
            "name": routine.name,
            "category": routine.category.value,
            "description": routine.description,
        }

        # Handle JSONB fields
        from planned.infrastructure.utils.serialization import dataclass_to_json_dict

        if routine.routine_schedule:
            row["routine_schedule"] = dataclass_to_json_dict(routine.routine_schedule)

        if routine.tasks:
            row["tasks"] = [dataclass_to_json_dict(task) for task in routine.tasks]

        return row
