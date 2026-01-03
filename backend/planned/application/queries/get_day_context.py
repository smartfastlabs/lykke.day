"""Query to get the complete context for a day."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, DayEntity, MessageEntity, TaskEntity, UserEntity

from .base import Query, QueryHandler


@dataclass(frozen=True)
class GetDayContextQuery(Query):
    """Query to get the complete context for a specific day.

    Returns a DayContext with day, tasks, calendar entries, and messages.
    If the day doesn't exist, returns a preview (unsaved) day.
    """

    user: UserEntity
    date: date


class GetDayContextHandler(QueryHandler[GetDayContextQuery, value_objects.DayContext]):
    """Handles GetDayContextQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: GetDayContextQuery) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            query: The query containing user and date

        Returns:
            A DayContext with all related data
        """
        async with self._uow_factory.create(query.user.id) as uow:
            tasks: list[TaskEntity] = []
            calendar_entries: list[CalendarEntryEntity] = []
            messages: list[MessageEntity] = []
            day: DayEntity

            try:
                # Try to load existing day and all related data
                day_id = DayEntity.id_from_date_and_user(query.date, query.user.id)
                tasks, calendar_entries, messages, day = await asyncio.gather(
                    uow.tasks.search_query(value_objects.DateQuery(date=query.date)),
                    uow.calendar_entries.search_query(value_objects.DateQuery(date=query.date)),
                    uow.messages.search_query(value_objects.DateQuery(date=query.date)),
                    uow.days.get(day_id),
                )
            except NotFoundError:
                # Day doesn't exist, create a preview day using default template
                day = await self._create_preview_day(uow, query.date, query.user.id, query.user)

            return self._build_context(day, tasks, calendar_entries, messages)

    async def _create_preview_day(
        self,
        uow: UnitOfWorkProtocol,
        date: date,
        user_id: UUID,
        user: UserEntity,
    ) -> DayEntity:
        """Create a preview day when no existing day is found.

        Args:
            uow: The unit of work
            date: The date for the preview day
            user_id: The user ID for the preview day
            user: The user entity

        Returns:
            A Day entity (not saved to database)
        """
        template_slug = user.settings.template_defaults[date.weekday()]
        template = await uow.day_templates.get_by_slug(template_slug)
        return DayEntity.create_for_date(
            date,
            user_id=user_id,
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

