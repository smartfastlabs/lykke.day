import uuid
from datetime import date as dt_date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from ..value_objects.day import DayStatus, DayTag
from .alarm import Alarm
from .base import BaseEntityObject
from .day_template import DayTemplate


class Day(BaseEntityObject):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    date: dt_date
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    tags: list[DayTag] = Field(default_factory=list)
    template: DayTemplate | None = None

    @model_validator(mode="after")
    def generate_id(self) -> "Day":
        """Generate deterministic UUID5 based on date and user_id.

        This ensures that Days with the same date and user_id always have
        the same ID, making lookups stable and deterministic.
        """
        self.id = self.id_from_date_and_user(self.date, self.user_id)
        return self

    @classmethod
    def id_from_date_and_user(cls, date: dt_date, user_id: UUID) -> UUID:
        """Generate deterministic UUID5 from date and user_id.

        This can be used to generate the ID for looking up a Day by date
        without creating a Day instance.
        """
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{user_id}:{date.isoformat()}"
        return uuid.uuid5(namespace, name)
