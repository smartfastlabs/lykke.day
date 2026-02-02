"""Query to get push notification context by ID."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects

if TYPE_CHECKING:
    from uuid import UUID

    from lykke.application.repositories import (
        PushNotificationRepositoryReadOnlyProtocol,
    )
    from lykke.domain.entities import CalendarEntryEntity, RoutineEntity, TaskEntity


@dataclass(frozen=True)
class GetPushNotificationContextQuery(Query):
    """Query to get a push notification context by ID."""

    push_notification_id: UUID


class GetPushNotificationContextHandler(
    BaseQueryHandler[
        GetPushNotificationContextQuery, value_objects.PushNotificationContext
    ]
):
    """Retrieves the referenced entity context for a push notification."""

    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol

    async def handle(
        self, query: GetPushNotificationContextQuery
    ) -> value_objects.PushNotificationContext:
        """Get referenced entities for a push notification."""
        notification = await self.push_notification_ro_repo.get(
            query.push_notification_id
        )

        task_ids: set[UUID] = set()
        routine_ids: set[UUID] = set()
        calendar_entry_ids: set[UUID] = set()

        for entity in notification.referenced_entities:
            if entity.entity_type == "task":
                task_ids.add(entity.entity_id)
            elif entity.entity_type == "routine":
                routine_ids.add(entity.entity_id)
            elif entity.entity_type == "calendar_entry":
                calendar_entry_ids.add(entity.entity_id)

        tasks: list[TaskEntity] = []
        if task_ids:
            tasks = await self.task_ro_repo.search(
                value_objects.TaskQuery(ids=list(task_ids))
            )

        async def safe_get_routine(routine_id: UUID) -> RoutineEntity | None:
            try:
                return await self.routine_ro_repo.get(routine_id)
            except NotFoundError:
                return None

        async def safe_get_calendar_entry(
            entry_id: UUID,
        ) -> CalendarEntryEntity | None:
            try:
                return await self.calendar_entry_ro_repo.get(entry_id)
            except NotFoundError:
                return None

        routines: list[RoutineEntity] = []
        if routine_ids:
            routine_results = await asyncio.gather(
                *(safe_get_routine(routine_id) for routine_id in routine_ids)
            )
            routines = [routine for routine in routine_results if routine is not None]

        calendar_entries: list[CalendarEntryEntity] = []
        if calendar_entry_ids:
            entry_results = await asyncio.gather(
                *(
                    safe_get_calendar_entry(entry_id)
                    for entry_id in calendar_entry_ids
                )
            )
            calendar_entries = [
                entry for entry in entry_results if entry is not None
            ]

        return value_objects.PushNotificationContext(
            notification=notification,
            tasks=tasks,
            routines=routines,
            calendar_entries=calendar_entries,
        )
