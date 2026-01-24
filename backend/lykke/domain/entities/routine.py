from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class RoutineEntity(BaseEntityObject, AuditableEntity):
    user_id: UUID
    date: dt_date
    routine_definition_id: UUID
    name: str
    category: value_objects.TaskCategory
    description: str = ""
    time_window: value_objects.TimeWindow | None = None
