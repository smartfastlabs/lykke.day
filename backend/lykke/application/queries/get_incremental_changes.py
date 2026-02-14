"""Query handler to get incremental changes since a timestamp."""

from dataclasses import dataclass
from datetime import date as dt_date, datetime
from typing import Any
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
from lykke.presentation.api.schemas.mappers import (
    map_calendar_entry_to_schema,
    map_day_to_schema,
    map_routine_to_schema,
    map_task_to_schema,
)
from lykke.presentation.api.schemas.websocket_message import EntityChangeSchema


@dataclass(frozen=True)
class GetIncrementalChangesQuery(Query):
    """Query to get incremental changes."""

    since: datetime
    date: dt_date


class GetIncrementalChangesHandler(
    BaseQueryHandler[
        GetIncrementalChangesQuery, tuple[list[EntityChangeSchema], datetime | None]
    ]
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
    ) -> tuple[list[EntityChangeSchema], datetime | None]:
        """Handle get incremental changes query."""
        return await self.get_incremental_changes(query.since, query.date)

    async def get_incremental_changes(
        self, since_timestamp: datetime, target_date: dt_date
    ) -> tuple[list[EntityChangeSchema], datetime | None]:
        """Legacy compatibility method retained for interface stability."""
        _ = since_timestamp, target_date
        return [], None

    async def _load_entity_data(
        self,
        entity_type: str,
        entity_id: UUID,
        *,
        _activity_type: str,
        user_timezone: str | None,
    ) -> dict[str, Any] | None:
        """Load the full entity data from the repository and convert to dict.

        Args:
            entity_type: The type of entity (task, calendar_entry, etc.)
            entity_id: The ID of the entity

        Returns:
            Dictionary representation of the entity, or None if not found
        """
        try:
            if entity_type == "task":
                task = await self.task_ro_repo.get(entity_id)
                if not task:
                    return None
                # Convert task entity to dict using schema mapper
                task_schema = map_task_to_schema(task, user_timezone=user_timezone)
                return task_schema.model_dump(mode="json")

            elif entity_type == "calendarentry":
                entry = await self.calendar_entry_ro_repo.get(entity_id)
                if not entry:
                    return None
                # Convert calendar entry to dict using schema mapper
                entry_schema = map_calendar_entry_to_schema(
                    entry, user_timezone=user_timezone
                )
                return entry_schema.model_dump(mode="json")

            elif entity_type == "routine":
                routine = await self.routine_ro_repo.get(entity_id)
                if not routine:
                    return None
                tasks = await self.task_ro_repo.search(
                    value_objects.TaskQuery(
                        date=routine.date,
                        routine_definition_ids=[routine.routine_definition_id],
                    )
                )
                routine_schema = map_routine_to_schema(
                    routine,
                    tasks=tasks,
                    user_timezone=user_timezone,
                )
                return routine_schema.model_dump(mode="json")

            elif entity_type == "day":
                day = await self.day_ro_repo.get(entity_id)
                if not day:
                    return None
                day_schema = map_day_to_schema(day)
                return day_schema.model_dump(mode="json")

            return None
        except Exception:
            return None
