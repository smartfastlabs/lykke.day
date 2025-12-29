import uuid
from datetime import date as dt_date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from ..value_objects.day import DayStatus, DayTag
from .alarm import Alarm
from .base import BaseObject


class DayTemplate(BaseObject):
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    tasks: list[str] = Field(default_factory=list)
    alarm: Alarm | None = None
    icon: str | None = None


class Day(BaseObject):
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    date: dt_date
    template_id: str = "default"
    tags: list[DayTag] = Field(default_factory=list)
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    @model_validator(mode="after")
    def generate_uuid(self) -> "Day":
        # Generate UUID5 based on date and user_uuid for deterministic IDs
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{self.user_uuid}:{self.date.isoformat()}"
        self.uuid = uuid.uuid5(namespace, name)
        return self
        return self
        return self
