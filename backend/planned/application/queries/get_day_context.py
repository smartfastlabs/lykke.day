"""Query to get the complete context for a day."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity, DayEntity, MessageEntity, TaskEntity, UserEntity


class GetDayContextHandler:
    """Gets the complete context for a day."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

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
        messages: list[MessageEntity] = []
        day: DayEntity

        try:
            # Try to load existing day and all related data
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            tasks, calendar_entries, messages, day = await asyncio.gather(
                self._ro_repos.task_ro_repo.search_query(value_objects.DateQuery(date=date)),
                self._ro_repos.calendar_entry_ro_repo.search_query(value_objects.DateQuery(date=date)),
                self._ro_repos.message_ro_repo.search_query(value_objects.DateQuery(date=date)),
                self._ro_repos.day_ro_repo.get(day_id),
            )
        except NotFoundError:
            # Day doesn't exist, create a preview day using default template
            user = await self._ro_repos.user_ro_repo.get(self.user_id)
            day = await self._create_preview_day(date, user)

        return self._build_context(day, tasks, calendar_entries, messages)

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
        template = await self._ro_repos.day_template_ro_repo.get_by_slug(template_slug)
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
        messages: list[MessageEntity],
    ) -> value_objects.DayContext:
        """Build a DayContext from loaded data.

        Args:
            day: The day entity
            tasks: List of tasks for the day
            calendar_entries: List of calendar entries for the day
            messages: List of messages for the day

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
            messages=messages,
        )

