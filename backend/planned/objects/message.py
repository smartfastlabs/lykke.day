from datetime import date as dt_date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import computed_field

from planned import settings

from .base import BaseObject


class Message(BaseObject):
    author: Literal["system", "agent", "user"]
    sent_at: datetime
    content: str
    read_at: datetime | None = None

    @computed_field  # mypy: ignore
    @property
    def date(self) -> dt_date:
        return self.starts_at.astimezone(ZoneInfo(settings.TIMEZONE)).date()
