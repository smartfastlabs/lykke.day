"""Query to get the complete context for a day."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import CalendarEntryEntity, DayEntity, MessageEntity, TaskEntity, UserEntity


class GetDayContextHandler:
    """Gets the complete context for a day."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_day_context(
        self, user: UserEntity, date: date
    ) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            user: The user entity
            date: The date to get context for

        Returns:
            A DayContext with all related data
        """
        async with self._uow_factory.create(user.id) as uow:
            tasks: list[TaskEntity] = []
            calendar_entries: list[CalendarEntryEntity] = []
            messages: list[MessageEntity] = []
            day: DayEntity

            try:
                # Try to load existing day and all related data
                day_id = DayEntity.id_from_date_and_user(date, user.id)
                tasks, calendar_entries, messages, day = await asyncio.gather(
                    uow.tasks.search_query(value_objects.DateQuery(date=date)),
                    uow.calendar_entries.search_query(value_objects.DateQuery(date=date)),
                    uow.messages.search_query(value_objects.DateQuery(date=date)),
                    uow.days.get(day_id),
                )
            except NotFoundError:
                # Day doesn't exist, create a preview day using default template
                day = await self._create_preview_day(uow, date, user.id, user)

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

