"""Query to preview what a day would look like if scheduled."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from loguru import logger

from planned.application.queries.preview_tasks import PreviewTasksHandler, PreviewTasksQuery
from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.exceptions import NotFoundError
from planned.domain import entities, value_objects

from .base import Query, QueryHandler


@dataclass(frozen=True)
class PreviewDayQuery(Query):
    """Query to preview what a day would look like if scheduled.

    Returns a DayContext with preview data (not saved to database).
    Useful for showing users what tasks would be created.
    """

    user_id: UUID
    date: date
    template_id: UUID | None = None


class PreviewDayHandler(QueryHandler[PreviewDayQuery, value_objects.DayContext]):
    """Handles PreviewDayQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._preview_tasks_handler = PreviewTasksHandler(uow_factory)

    async def handle(self, query: PreviewDayQuery) -> value_objects.DayContext:
        """Preview what a day would look like if scheduled.

        Args:
            query: The query containing user_id, date, and optional template_id

        Returns:
            A DayContext with preview data (not saved)
        """
        async with self._uow_factory.create(query.user_id) as uow:
            # Get template
            template = await self._get_template(uow, query)

            # Create preview day
            day = entities.Day.create_for_date(
                query.date,
                user_id=query.user_id,
                template=template,
            )

            # Load preview tasks and existing data in parallel
            preview_tasks_query = PreviewTasksQuery(
                user_id=query.user_id,
                date=query.date,
            )
            tasks, calendar_entries, messages = await asyncio.gather(
                self._preview_tasks_handler.handle(preview_tasks_query),
                uow.calendar_entries.search_query(value_objects.DateQuery(date=query.date)),
                uow.messages.search_query(value_objects.DateQuery(date=query.date)),
            )

            return value_objects.DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=calendar_entries,
                messages=messages,
            )

    async def _get_template(
        self,
        uow: UnitOfWorkProtocol,
        query: PreviewDayQuery,
    ) -> entities.DayTemplate:
        """Get the template to use for the preview."""
        if query.template_id is not None:
            return await uow.day_templates.get(query.template_id)

        # Try to get from existing day
        try:
            day_id = entities.Day.id_from_date_and_user(query.date, query.user_id)
            existing_day = await uow.days.get(day_id)
            if existing_day.template:
                return existing_day.template
        except NotFoundError:
            pass

        # Fall back to user's default template
        user = await uow.users.get(query.user_id)
        template_slug = user.settings.template_defaults[query.date.weekday()]
        return await uow.day_templates.get_by_slug(template_slug)

