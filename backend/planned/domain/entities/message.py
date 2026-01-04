from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from .base import BaseEntityObject


@dataclass(kw_only=True)
class MessageEntity(BaseEntityObject):
    user_id: UUID
    author: Literal["system", "agent", "user"]
    sent_at: datetime
    content: str
    read_at: datetime | None = None
