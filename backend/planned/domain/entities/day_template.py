import uuid
from uuid import UUID

from pydantic import Field, model_validator

from .alarm import Alarm
from .base import BaseEntityObject


class DayTemplate(BaseEntityObject):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    slug: str
    alarm: Alarm | None = None
    icon: str | None = None
    routine_ids: list[UUID] = Field(default_factory=list)

    @classmethod
    def id_from_slug_and_user(cls, slug: str, user_id: UUID) -> UUID:
        """Generate deterministic UUID5 from slug and user_id.

        This can be used to generate the ID for looking up a DayTemplate by slug
        without creating a DayTemplate instance.
        """
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{user_id}:{slug}"
        return uuid.uuid5(namespace, name)

    @model_validator(mode="after")
    def generate_id(self) -> "DayTemplate":
        """Generate deterministic UUID5 based on slug and user_id.

        This ensures that DayTemplates with the same slug and user_id always have
        the same ID, making lookups stable and deterministic.
        """
        # Always regenerate ID for determinism (overrides default_factory)
        self.id = self.id_from_slug_and_user(self.slug, self.user_id)
        return self
