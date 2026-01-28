from typing import Any

from sqlalchemy.sql import Select

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects.task import TaskCategory
from lykke.infrastructure.database.tables import routines_tbl
from lykke.infrastructure.repositories.base.utils import (
    convert_enum_fields,
    convert_time_fields,
    ensure_datetimes_utc,
    enum_to_value,
    filter_init_false_fields,
)

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
            "category": enum_to_value(routine.category),
            "description": routine.description,
            "status": enum_to_value(routine.status),
            "snoozed_until": routine.snoozed_until,
        }

        if routine.time_window:
            row["time_window"] = dataclass_to_json_dict(routine.time_window)

        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> RoutineEntity:
        """Convert a database row dict to a Routine entity."""
        data = filter_init_false_fields(dict(row), RoutineEntity)

        # Convert enum fields
        data = convert_enum_fields(data, {
            "category": TaskCategory,
            "status": value_objects.TaskStatus,
        })

        # Handle time_window JSONB field
        time_window = data.get("time_window")
        if time_window:
            time_window = convert_time_fields(
                time_window,
                ["available_time", "start_time", "end_time", "cutoff_time"],
            )
            data["time_window"] = value_objects.TimeWindow(**time_window)

        data = ensure_datetimes_utc(data, keys=("snoozed_until",))
        return RoutineEntity(**data)
