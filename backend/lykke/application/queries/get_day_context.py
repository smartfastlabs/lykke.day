"""Query to get the complete context for a day."""

import asyncio
from dataclasses import dataclass
from datetime import date as datetime_date
from typing import cast

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.core.constants import DEFAULT_END_OF_DAY_TIME
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity, DayEntity, TaskEntity


@dataclass(frozen=True)
class GetDayContextQuery(Query):
    """Query to get day context."""

    date: datetime_date


class GetDayContextHandler(
    BaseQueryHandler[GetDayContextQuery, value_objects.DayContext]
):
    """Gets the complete context for a day."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayContextQuery) -> value_objects.DayContext:
        """Handle get day context query."""
        return await self.get_day_context(query.date)

    async def get_day_context(self, date: datetime_date) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            date: The date to get context for

        Returns:
            A DayContext with all related data
        """
        day_id = DayEntity.id_from_date_and_user(date, self.user_id)

        tasks_result, calendar_entries_result, day_result = await asyncio.gather(
            self.task_ro_repo.search(value_objects.TaskQuery(date=date)),
            self.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(date=date)
            ),
            self.day_ro_repo.get(day_id),
            return_exceptions=True,
        )

        tasks = cast(
            "list[TaskEntity]", self._unwrap_result(tasks_result, "tasks result")
        )
        calendar_entries = cast(
            "list[CalendarEntryEntity]",
            self._unwrap_result(calendar_entries_result, "calendar entries result"),
        )

        if isinstance(day_result, NotFoundError):
            raise day_result
        elif isinstance(day_result, Exception):
            # Propagate other errors to maintain existing error handling behaviour
            raise day_result
        else:
            if not isinstance(day_result, DayEntity):
                raise TypeError(
                    f"Unexpected day result type: {type(day_result).__name__}"
                )
            day = day_result

        return self._build_context(day, tasks, calendar_entries)

    @staticmethod
    def _unwrap_result(result: object, name: str) -> object:
        """Raise any exception returned by asyncio.gather."""
        if isinstance(result, Exception):
            raise type(result)(f"{name}: {result}") from result
        return result

    def _build_context(
        self,
        day: DayEntity,
        tasks: list[TaskEntity],
        calendar_entries: list[CalendarEntryEntity],
    ) -> value_objects.DayContext:
        """Build a DayContext from loaded data.

        Args:
            day: The day entity
            tasks: List of tasks for the day
            calendar_entries: List of calendar entries for the day

        Returns:
            A DayContext with sorted tasks and calendar entries
        """
        return value_objects.DayContext(
            day=day,
            tasks=sorted(
                tasks,
                key=lambda x: x.schedule.start_time
                if x.schedule and x.schedule.start_time
                else DEFAULT_END_OF_DAY_TIME,
            ),
            calendar_entries=sorted(calendar_entries, key=lambda e: e.starts_at),
        )
