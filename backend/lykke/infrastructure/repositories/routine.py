from datetime import time
from typing import Any

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects.task import TaskCategory
from lykke.infrastructure.database.tables import routines_tbl
from lykke.infrastructure.repositories.base.utils import filter_init_false_fields

from .base import UserScopedBaseRepository


class RoutineRepository(UserScopedBaseRepository[RoutineEntity, value_objects.RoutineQuery]):
    Object = RoutineEntity
    table = routines_tbl
    QueryClass = value_objects.RoutineQuery

    def build_query(self, query: value_objects.RoutineQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        if query.routine_definition_ids:
            stmt = stmt.where(
                self.table.c.routine_definition_id.in_(
                    query.routine_definition_ids
                )
            )

        return stmt

    @staticmethod
    def entity_to_row(routine: RoutineEntity) -> dict[str, Any]:
        """Convert a Routine entity to a database row dict."""
        row: dict[str, Any] = {
            "id": routine.id,
            "user_id": routine.user_id,
            "date": routine.date,
            "routine_definition_id": routine.routine_definition_id,
            "name": routine.name,
            "category": routine.category.value
            if hasattr(routine.category, "value")
            else routine.category,
            "description": routine.description,
        }

        if routine.time_window:
            row["time_window"] = dataclass_to_json_dict(routine.time_window)

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> RoutineEntity:
        """Convert a database row dict to a Routine entity."""
        data = filter_init_false_fields(dict(row), RoutineEntity)

        category = data.get("category")
        if isinstance(category, str):
            data["category"] = TaskCategory(category)

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

        return RoutineEntity(**data)
