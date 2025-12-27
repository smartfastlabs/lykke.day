from datetime import date as dt_date, datetime
from typing import Literal

from pydantic import computed_field

from .base import BaseDateObject


class Message(BaseDateObject):
    author: Literal["system", "agent", "user"]
    sent_at: datetime
    content: str
    read_at: datetime | None = None

    def _get_datetime(self) -> datetime:
        return self.sent_at
