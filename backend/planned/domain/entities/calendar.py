import uuid
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ..events.calendar_events import CalendarUpdatedEvent
from ..value_objects.update import CalendarUpdateObject
from .base import BaseEntityObject


@dataclass(kw_only=True)
class CalendarEntity(BaseEntityObject[CalendarUpdateObject, CalendarUpdatedEvent]):
    user_id: UUID
    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # Generate UUID5 based on platform and platform_id for deterministic IDs
        # Only generates if id was not explicitly provided
        # Check if id needs to be generated (mypy doesn't understand field override)
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
            name = f"{self.platform}:{self.platform_id}"
            generated_id = uuid.uuid5(namespace, name)
            object.__setattr__(self, "id", generated_id)
        # After this point, self.id is guaranteed to be a UUID
