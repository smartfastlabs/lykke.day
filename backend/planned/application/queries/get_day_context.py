"""Query to get the complete context for a day."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity, DayEntity, TaskEntity, UserEntity


class GetDayContextHandler(BaseQueryHandler):
    """Gets the complete context for a day."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    async def get_day_context(
        self, date: date
    ) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            date: The date to get context for

        Returns:
            A DayContext with all related data
        """
        tasks: list[TaskEntity] = []
        calendar_entries: list[CalendarEntryEntity] = []
        day: DayEntity

        try:
            # Try to load existing day and all related data
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            tasks, calendar_entries, day = await asyncio.gather(
                self.task_ro_repo.search_query(value_objects.DateQuery(date=date)),
                self.calendar_entry_ro_repo.search_query(value_objects.DateQuery(date=date)),
                self.day_ro_repo.get(day_id),
            )
        except NotFoundError:
            # Day doesn't exist, create a preview day using default template
            user = await self.user_ro_repo.get(self.user_id)
            day = await self._create_preview_day(date, user)

        return self._build_context(day, tasks, calendar_entries)

    async def _create_preview_day(
        self,
        date: date,
        user: UserEntity,
    ) -> DayEntity:
        """Create a preview day when no existing day is found.

        Args:
            date: The date for the preview day
            user: The user entity

        Returns:
            A Day entity (not saved to database)
        """
        template_slug = user.settings.template_defaults[date.weekday()]
        template = await self.day_template_ro_repo.get_by_slug(template_slug)
        return DayEntity.create_for_date(
            date,
            user_id=self.user_id,
            template=template,
        )

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

