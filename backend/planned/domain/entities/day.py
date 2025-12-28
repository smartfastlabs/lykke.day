from datetime import date as dt_date, datetime
from uuid import UUID

from pydantic import Field

from ..value_objects.day import DayStatus, DayTag
from .alarm import Alarm
from .base import BaseConfigObject


class DayTemplate(BaseConfigObject):
    user_uuid: UUID
    tasks: list[str] = Field(default_factory=list)
    alarm: Alarm | None = None
    icon: str | None = None


class Day(BaseConfigObject):
    user_uuid: UUID
    date: dt_date
    template_id: str = "default"
    tags: list[DayTag] = Field(default_factory=list)
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    def model_post_init(self, __context__=None) -> None:  # type: ignore
        self.id = str(self.date)
