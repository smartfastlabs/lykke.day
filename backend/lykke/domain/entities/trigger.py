from dataclasses import dataclass
from uuid import UUID

from lykke.domain.entities.base import BaseEntityObject


@dataclass(kw_only=True)
class TriggerEntity(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
