from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime
    from uuid import UUID

    from lykke.domain.entities.routine_definition import RoutineDefinitionEntity


@dataclass(kw_only=True)
class RoutineEntity(BaseEntityObject):
    user_id: UUID
    date: dt_date
    routine_definition_id: UUID
    name: str
    category: value_objects.TaskCategory
    description: str = ""
    status: value_objects.TaskStatus = value_objects.TaskStatus.NOT_STARTED
    snoozed_until: datetime | None = None
    time_window: value_objects.TimeWindow | None = None

    @classmethod
    def from_definition(
        cls,
        routine_definition: RoutineDefinitionEntity,
        date: dt_date,
        user_id: UUID,
    ) -> RoutineEntity:
        """Build a RoutineEntity from a RoutineDefinitionEntity for a given date and user."""
        return cls(
            user_id=user_id,
            date=date,
            routine_definition_id=routine_definition.id,
            name=routine_definition.name,
            category=routine_definition.category,
            description=routine_definition.description,
            time_window=routine_definition.time_window,
        )
