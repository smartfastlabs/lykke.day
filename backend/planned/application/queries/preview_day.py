"""Query to preview what a day would look like if scheduled."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.queries.base import BaseQueryHandler
from planned.application.queries.preview_tasks import PreviewTasksHandler
from planned.application.repositories import (
    CalendarEntryRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from planned.application.unit_of_work import ReadOnlyRepositories
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import DayEntity, DayTemplateEntity


class PreviewDayHandler(BaseQueryHandler):
    """Previews what a day would look like if scheduled."""

    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        super().__init__(ro_repos, user_id)
        self._preview_tasks_handler = PreviewTasksHandler(ro_repos, user_id)

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
        tasks, calendar_entries, messages = await asyncio.gather(
            self._preview_tasks_handler.preview_tasks(date),
            self.calendar_entry_ro_repo.search_query(value_objects.DateQuery(date=date)),
            self.message_ro_repo.search_query(value_objects.DateQuery(date=date)),
        )

        return value_objects.DayContext(
            day=day,
            tasks=tasks,
            calendar_entries=calendar_entries,
            messages=messages,
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
        return await self.day_template_ro_repo.get_by_slug(template_slug)

