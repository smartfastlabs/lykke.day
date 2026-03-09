from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from .day import DayEntity


@dataclass(kw_only=True)
class HasDateMixin:
    """Shared day-scoped fields/behavior for entities."""

    day_id: UUID | None = None

    def resolve_day_id(self) -> UUID:
        """Return day_id, computing it from user_id + date when missing."""
        if self.day_id is not None:
            return self.day_id

        date_value = getattr(self, "date", None)
        user_id = getattr(self, "user_id", None)
        if not isinstance(date_value, dt_date) or not isinstance(user_id, UUID):
            raise ValueError("HasDateMixin requires `date` and `user_id` to resolve day_id")

        self.day_id = DayEntity.id_from_date_and_user(date_value, user_id)
        return self.day_id
