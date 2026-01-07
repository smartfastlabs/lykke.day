from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.value_objects.update import DayTemplateUpdateObject

from .base import BaseEntityObject

if TYPE_CHECKING:
    from lykke.domain.events.day_template_events import DayTemplateUpdatedEvent


@dataclass(kw_only=True)
class DayTemplateEntity(BaseEntityObject[DayTemplateUpdateObject, "DayTemplateUpdatedEvent"]):
    user_id: UUID
    slug: str
    alarm: value_objects.Alarm | None = None
    icon: str | None = None
    routine_ids: list[UUID] = field(default_factory=list)
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Generate deterministic UUID5 based on slug and user_id."""
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            generated_id = self.id_from_slug_and_user(self.slug, self.user_id)
            object.__setattr__(self, "id", generated_id)

    @classmethod
    def id_from_slug_and_user(cls, slug: str, user_id: UUID) -> UUID:
        """Generate deterministic UUID5 from slug and user_id."""
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.day")
        name = f"{user_id}:{slug}"
        return uuid.uuid5(namespace, name)

    def _copy_with_routine_ids(self, routine_ids: list[UUID]) -> DayTemplateEntity:
        """Return a copy of this day template with updated routine_ids."""
        return DayTemplateEntity(
            id=self.id,
            user_id=self.user_id,
            slug=self.slug,
            alarm=self.alarm,
            icon=self.icon,
            routine_ids=routine_ids,
        )

    def add_routine(self, routine_id: UUID) -> DayTemplateEntity:
        """Attach a routine to the day template, enforcing uniqueness."""
        if routine_id in self.routine_ids:
            raise DomainError("Routine already attached to day template")

        updated = self._copy_with_routine_ids([*self.routine_ids, routine_id])
        from lykke.domain.events.day_template_events import (
            DayTemplateRoutineAddedEvent,
        )

        updated._add_event(
            DayTemplateRoutineAddedEvent(
                day_template_id=updated.id, routine_id=routine_id
            )
        )
        return updated

    def remove_routine(self, routine_id: UUID) -> DayTemplateEntity:
        """Detach a routine from the day template."""
        if routine_id not in self.routine_ids:
            raise NotFoundError("Routine not found in day template")

        updated = self._copy_with_routine_ids(
            [rid for rid in self.routine_ids if rid != routine_id]
        )
        from lykke.domain.events.day_template_events import (
            DayTemplateRoutineRemovedEvent,
        )

        updated._add_event(
            DayTemplateRoutineRemovedEvent(
                day_template_id=updated.id, routine_id=routine_id
            )
        )
        return updated

