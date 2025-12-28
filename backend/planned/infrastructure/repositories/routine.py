from typing import Any

from planned.domain.entities.routine import Routine

from .base import BaseConfigRepository
from .base.schema import routines


class RoutineRepository(BaseConfigRepository[Routine]):
    Object = Routine
    table = routines

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
            row["routine_schedule"] = routine.routine_schedule.model_dump()

        if routine.tasks:
            row["tasks"] = [task.model_dump() for task in routine.tasks]

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Routine:
        """Convert a database row dict to a Routine entity."""
        return Routine.model_validate(row, from_attributes=True)
