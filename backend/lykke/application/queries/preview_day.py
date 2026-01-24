"""Query to preview what a day would look like if scheduled."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.preview_tasks import (
    PreviewTasksHandler,
    PreviewTasksQuery,
)
from lykke.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class PreviewDayQuery(Query):
    """Query to preview a day."""

    date: date
    template_id: UUID | None = None


class PreviewDayHandler(BaseQueryHandler[PreviewDayQuery, value_objects.DayContext]):
    """Previews what a day would look like if scheduled."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        super().__init__(ro_repos, user_id)
        self._preview_tasks_handler = PreviewTasksHandler(ro_repos, user_id)

    async def handle(self, query: PreviewDayQuery) -> value_objects.DayContext:
        """Handle preview day query."""
        return await self.preview_day(query.date, query.template_id)

    async def preview_day(
        self, date: date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Preview what a day would look like if scheduled.

        Args:
            date: The date to preview
            template_id: Optional template ID to use

        Returns:
            A DayContext with preview data (not saved)
        """
        # Get template
        template = await self._get_template(date, template_id)

        # Create preview day
        day = DayEntity.create_for_date(
            date,
            user_id=self.user_id,
            template=template,
        )

        # Load preview tasks and existing data in parallel
        tasks, calendar_entries = await asyncio.gather(
            self._preview_tasks_handler.handle(PreviewTasksQuery(date=date)),
            self.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(date=date)
            ),
        )

        return value_objects.DayContext(
            day=day,
            tasks=tasks,
            calendar_entries=calendar_entries,
        )

    async def _get_template(
        self,
        date: date,
        template_id: UUID | None,
    ) -> DayTemplateEntity:
        """Get the template to use for the preview."""
        if template_id is not None:
            return await self.day_template_ro_repo.get(template_id)

        # Try to get from existing day
        try:
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            existing_day = await self.day_ro_repo.get(day_id)
            if existing_day.template:
                return existing_day.template
        except NotFoundError:
            pass

        # Fall back to user's default template
        user = await self.user_ro_repo.get(self.user_id)
        template_slug = user.settings.template_defaults[date.weekday()]
        return await self.day_template_ro_repo.search_one(
            value_objects.DayTemplateQuery(slug=template_slug)
        )
