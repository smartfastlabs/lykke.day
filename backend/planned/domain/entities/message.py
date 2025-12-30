from datetime import datetime
from typing import Literal
from uuid import UUID

from .base import BaseDateObject


class Message(BaseDateObject):
    user_id: UUID
    author: Literal["system", "agent", "user"]
    sent_at: datetime
    content: str
    read_at: datetime | None = None

    def _get_datetime(self) -> datetime:
        return self.sent_at
