"""Query handler to get incremental changes since a timestamp."""

from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import Union
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    BrainDumpRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    RoutineDefinitionRepositoryReadOnlyProtocol,
    RoutineRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import (
    CalendarEntryEntity,
    DayEntity,
    RoutineEntity,
    TaskEntity,
)


@dataclass(frozen=True)
class EntityLoadResult:
    """Application-level result for loading a single entity for incremental sync.

    Presentation layer uses this to build EntityChangeSchema (mappers stay in presentation).
    """

    entity_type: str
    entity: Union[TaskEntity, CalendarEntryEntity, RoutineEntity, DayEntity]
    tasks: list[TaskEntity] | None = None  # Only set for entity_type == "routine"


@dataclass(frozen=True)
class GetIncrementalChangesQuery(Query):
    """Query to get incremental changes."""

    since: datetime
    date: dt_date


@dataclass(frozen=True)
class GetIncrementalChangesResult:
    """Result of GetIncrementalChangesQuery. Use a dataclass for handler return types."""

    changes: list[dict[str, object]]
    last_timestamp: datetime | None


class GetIncrementalChangesHandler(
    BaseQueryHandler[GetIncrementalChangesQuery, GetIncrementalChangesResult]
):
    """Provides entity data loading for incremental change payloads."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetIncrementalChangesQuery
    ) -> GetIncrementalChangesResult:
        """Handle get incremental changes query."""
        return await self.get_incremental_changes(query.since, query.date)

    async def get_incremental_changes(
        self, since_timestamp: datetime, target_date: dt_date
    ) -> GetIncrementalChangesResult:
        """Legacy compatibility method retained for interface stability."""
        _ = since_timestamp, target_date
        return GetIncrementalChangesResult(changes=[], last_timestamp=None)

    async def load_entity_for_sync(
        self,
        entity_type: str,
        entity_id: UUID,
        *,
        user_timezone: str | None = None,
    ) -> EntityLoadResult | None:
        """Load entity (and related data for routine) for incremental sync.

        Returns application-level EntityLoadResult. Presentation layer converts
        to wire format via mappers and EntityChangeSchema.
        """
        try:
            if entity_type == "task":
                task = await self.task_ro_repo.get(entity_id)
                if not task:
                    return None
                return EntityLoadResult(entity_type=entity_type, entity=task)

            if entity_type == "calendarentry":
                entry = await self.calendar_entry_ro_repo.get(entity_id)
                if not entry:
                    return None
                return EntityLoadResult(entity_type=entity_type, entity=entry)

            if entity_type == "routine":
                routine = await self.routine_ro_repo.get(entity_id)
                if not routine:
                    return None
                tasks = await self.task_ro_repo.search(
                    value_objects.TaskQuery(
                        date=routine.date,
                        routine_definition_ids=[routine.routine_definition_id],
                    )
                )
                return EntityLoadResult(
                    entity_type=entity_type, entity=routine, tasks=tasks
                )

            if entity_type == "day":
                day = await self.day_ro_repo.get(entity_id)
                if not day:
                    return None
                return EntityLoadResult(entity_type=entity_type, entity=day)

            return None
        except Exception:
            return None
