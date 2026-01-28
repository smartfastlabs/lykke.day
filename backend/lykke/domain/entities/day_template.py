from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import time as dt_time  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID

from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.events.day_template_events import (
    DayTemplateRoutineDefinitionAddedEvent,
    DayTemplateRoutineDefinitionRemovedEvent,
    DayTemplateTimeBlockAddedEvent,
    DayTemplateTimeBlockRemovedEvent,
)
from lykke.domain.value_objects.update import DayTemplateUpdateObject

from .base import BaseEntityObject

if TYPE_CHECKING:
    from lykke.domain.events.day_template_events import DayTemplateUpdatedEvent

VALUE_OBJECTS = value_objects


@dataclass(kw_only=True)
class DayTemplateEntity(
    BaseEntityObject[DayTemplateUpdateObject, "DayTemplateUpdatedEvent"]
):
    user_id: UUID
    slug: str
    start_time: dt_time | None = None
    end_time: dt_time | None = None
    icon: str | None = None
    routine_definition_ids: list[UUID] = field(default_factory=list)
    time_blocks: list[value_objects.DayTemplateTimeBlock] = field(default_factory=list)
    alarms: list[value_objects.Alarm] = field(default_factory=list)
    high_level_plan: value_objects.HighLevelPlan | None = None
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

    def _copy_with_routine_definition_ids(
        self, routine_definition_ids: list[UUID]
    ) -> DayTemplateEntity:
        """Return a copy of this day template with updated routine_definition_ids."""
        return DayTemplateEntity(
            id=self.id,
            user_id=self.user_id,
            slug=self.slug,
            start_time=self.start_time,
            end_time=self.end_time,
            icon=self.icon,
            routine_definition_ids=routine_definition_ids,
            time_blocks=self.time_blocks,
            alarms=self.alarms,
            high_level_plan=self.high_level_plan,
        )

    def add_routine_definition(self, routine_definition_id: UUID) -> DayTemplateEntity:
        """Attach a routine definition to the day template, enforcing uniqueness."""
        if routine_definition_id in self.routine_definition_ids:
            raise DomainError("Routine definition already attached to day template")

        updated = self._copy_with_routine_definition_ids(
            [*self.routine_definition_ids, routine_definition_id]
        )
        updated._add_event(
            DayTemplateRoutineDefinitionAddedEvent(
                user_id=self.user_id,
                day_template_id=updated.id,
                routine_definition_id=routine_definition_id,
            )
        )
        return updated

    def remove_routine_definition(
        self, routine_definition_id: UUID
    ) -> DayTemplateEntity:
        """Detach a routine definition from the day template."""
        if routine_definition_id not in self.routine_definition_ids:
            raise NotFoundError("Routine definition not found in day template")

        updated = self._copy_with_routine_definition_ids(
            [rid for rid in self.routine_definition_ids if rid != routine_definition_id]
        )
        updated._add_event(
            DayTemplateRoutineDefinitionRemovedEvent(
                user_id=self.user_id,
                day_template_id=updated.id,
                routine_definition_id=routine_definition_id,
            )
        )
        return updated

    def _copy_with_time_blocks(
        self, time_blocks: list[value_objects.DayTemplateTimeBlock]
    ) -> DayTemplateEntity:
        """Return a copy of this day template with updated time_blocks."""
        return DayTemplateEntity(
            id=self.id,
            user_id=self.user_id,
            slug=self.slug,
            start_time=self.start_time,
            end_time=self.end_time,
            icon=self.icon,
            routine_definition_ids=self.routine_definition_ids,
            time_blocks=time_blocks,
            alarms=self.alarms,
            high_level_plan=self.high_level_plan,
        )

    def add_time_block(
        self, time_block: value_objects.DayTemplateTimeBlock
    ) -> DayTemplateEntity:
        """Add a time block to the day template."""
        # Check for overlapping time blocks
        for existing_block in self.time_blocks:
            if (
                time_block.start_time < existing_block.end_time
                and time_block.end_time > existing_block.start_time
            ):
                raise DomainError("Time block overlaps with existing time block")

        updated = self._copy_with_time_blocks([*self.time_blocks, time_block])
        updated._add_event(
            DayTemplateTimeBlockAddedEvent(
                user_id=self.user_id,
                day_template_id=updated.id,
                time_block_definition_id=time_block.time_block_definition_id,
                start_time=time_block.start_time,
                end_time=time_block.end_time,
            )
        )
        return updated

    def remove_time_block(
        self, time_block_definition_id: UUID, start_time: dt_time
    ) -> DayTemplateEntity:
        """Remove a time block from the day template."""
        # Find the time block to remove
        time_block_to_remove = None
        for tb in self.time_blocks:
            if (
                tb.time_block_definition_id == time_block_definition_id
                and tb.start_time == start_time
            ):
                time_block_to_remove = tb
                break

        if time_block_to_remove is None:
            raise NotFoundError("Time block not found in day template")

        updated = self._copy_with_time_blocks(
            [tb for tb in self.time_blocks if tb != time_block_to_remove]
        )
        updated._add_event(
            DayTemplateTimeBlockRemovedEvent(
                user_id=self.user_id,
                day_template_id=updated.id,
                time_block_definition_id=time_block_definition_id,
                start_time=start_time,
            )
        )
        return updated
