from typing import Any

from planned.domain.entities.routine import Routine

from .base import BaseQuery, BaseRepository
from .base.schema import routines
from .base.utils import normalize_list_fields


class RoutineRepository(BaseRepository[Routine, BaseQuery]):
    Object = Routine
    table = routines
    QueryClass = BaseQuery

    @staticmethod
    def entity_to_row(routine: Routine) -> dict[str, Any]:
        """Convert a Routine entity to a database row dict."""
        row: dict[str, Any] = {
            "id": routine.id,
            "name": routine.name,
            "category": routine.category.value,
            "description": routine.description,
        }

        # Handle JSONB fields
        if routine.routine_schedule:
            row["routine_schedule"] = routine.routine_schedule.model_dump(mode="json")

        if routine.tasks:
            row["tasks"] = [task.model_dump(mode="json") for task in routine.tasks]

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Routine:
        """Convert a database row dict to a Routine entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, Routine)
        return Routine.model_validate(data, from_attributes=True)
