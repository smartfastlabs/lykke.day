from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ..value_objects.task import EventCategory, TaskFrequency
from .base import BaseEntityObject


@dataclass(kw_only=True)
class CalendarEntrySeriesEntity(BaseEntityObject):
    user_id: UUID
    calendar_id: UUID
    name: str
    platform_id: str
    platform: str
    frequency: TaskFrequency
    event_category: EventCategory | None = None
    recurrence: list[str] = field(default_factory=list)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Ensure deterministic ID based on platform source."""
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            generated_id = self.id_from_platform(self.platform, self.platform_id)
            object.__setattr__(self, "id", generated_id)

    @classmethod
    def id_from_platform(cls, platform: str, platform_id: str) -> UUID:
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.calendar_entry_series")
        name = f"{platform}:{platform_id}"
        return uuid.uuid5(namespace, name)
