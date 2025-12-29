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
    slug: str
    tasks: list[str] = Field(default_factory=list)
    alarm: Alarm | None = None
    icon: str | None = None

    @classmethod
    def uuid_from_slug_and_user(cls, slug: str, user_uuid: UUID) -> UUID:
        """Generate deterministic UUID5 from slug and user_uuid.

        This can be used to generate the UUID for looking up a DayTemplate by slug
        without creating a DayTemplate instance.
        """
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{user_uuid}:{slug}"
        return uuid.uuid5(namespace, name)

    @model_validator(mode="after")
    def generate_uuid(self) -> "DayTemplate":
        """Generate deterministic UUID5 based on slug and user_uuid.

        This ensures that DayTemplates with the same slug and user_uuid always have
        the same UUID, making lookups stable and deterministic.
        """
        # Always regenerate UUID for determinism (overrides default_factory)
        self.uuid = self.uuid_from_slug_and_user(self.slug, self.user_uuid)
        return self


class Day(BaseObject):
    uuid: UUID = Field(default_factory=uuid.uuid4)
    user_uuid: UUID
    date: dt_date
    template_uuid: UUID
    tags: list[DayTag] = Field(default_factory=list)
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    @classmethod
    def uuid_from_date_and_user(cls, date: dt_date, user_uuid: UUID) -> UUID:
        """Generate deterministic UUID5 from date and user_uuid.

        This can be used to generate the UUID for looking up a Day by date
        without creating a Day instance.
        """
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{user_uuid}:{date.isoformat()}"
        return uuid.uuid5(namespace, name)

    @model_validator(mode="after")
    def generate_uuid(self) -> "Day":
        """Generate deterministic UUID5 based on date and user_uuid.

        This ensures that Days with the same date and user_uuid always have
        the same UUID, making lookups stable and deterministic.
        """
        self.uuid = self.uuid_from_date_and_user(self.date, self.user_uuid)
        return self
        return self
