"""Brain dump entity for quick capture items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.events.day_events import (
    BrainDumpItemAddedEvent,
    BrainDumpItemRemovedEvent,
    BrainDumpItemStatusChangedEvent,
    BrainDumpItemTypeChangedEvent,
)

from .base import BaseEntityObject


@dataclass(kw_only=True)
class BrainDumpEntity(BaseEntityObject):
    """Brain dump entity representing a single captured item."""

    user_id: UUID
    date: dt_date
    text: str
    status: value_objects.BrainDumpItemStatus = value_objects.BrainDumpItemStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    type: value_objects.BrainDumpItemType = value_objects.BrainDumpItemType.GENERAL

    def mark_added(self) -> None:
        """Record a brain dump item creation event."""
        self._add_event(
            BrainDumpItemAddedEvent(
                user_id=self.user_id,
                day_id=self._get_day_id(),
                date=self.date,
                item_id=self.id,
                item_text=self.text,
                entity_id=self._get_day_id(),
                entity_type="day",
                entity_date=self.date,
            )
        )

    def update_status(
        self, status: value_objects.BrainDumpItemStatus
    ) -> BrainDumpEntity:
        """Update the status of a brain dump item."""
        if status == self.status:
            return self

        updated = self.clone(status=status)
        updated._add_event(
            BrainDumpItemStatusChangedEvent(
                user_id=self.user_id,
                day_id=self._get_day_id(),
                date=self.date,
                item_id=self.id,
                old_status=self.status,
                new_status=status,
                item_text=self.text,
                entity_id=self._get_day_id(),
                entity_type="day",
                entity_date=self.date,
            )
        )
        return updated

    def update_type(
        self, item_type: value_objects.BrainDumpItemType
    ) -> BrainDumpEntity:
        """Update the type of a brain dump item."""
        if item_type == self.type:
            return self

        updated = self.clone(type=item_type)
        updated._add_event(
            BrainDumpItemTypeChangedEvent(
                user_id=self.user_id,
                day_id=self._get_day_id(),
                date=self.date,
                item_id=self.id,
                old_type=self.type,
                new_type=item_type,
                item_text=self.text,
                entity_id=self._get_day_id(),
                entity_type="day",
                entity_date=self.date,
            )
        )
        return updated

    def mark_removed(self) -> None:
        """Record a brain dump item removal event."""
        self._add_event(
            BrainDumpItemRemovedEvent(
                user_id=self.user_id,
                day_id=self._get_day_id(),
                date=self.date,
                item_id=self.id,
                item_text=self.text,
                entity_id=self._get_day_id(),
                entity_type="day",
                entity_date=self.date,
            )
        )

    def _get_day_id(self) -> UUID:
        from .day import DayEntity

        return DayEntity.id_from_date_and_user(self.date, self.user_id)
