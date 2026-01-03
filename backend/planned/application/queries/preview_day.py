"""Query to preview what a day would look like if scheduled."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.queries.preview_tasks import PreviewTasksHandler
from planned.application.unit_of_work import ReadOnlyRepositories
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import DayEntity, DayTemplateEntity


class PreviewDayHandler:
    """Previews what a day would look like if scheduled."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos
        self._preview_tasks_handler = PreviewTasksHandler(ro_repos)

    async def preview_day(
        self, user_id: UUID, date: date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Preview what a day would look like if scheduled.

        Args:
            user_id: The user ID
            date: The date to preview
            template_id: Optional template ID to use

        Returns:
            A DayContext with preview data (not saved)
        """
        # Get template
        template = await self._get_template(user_id, date, template_id)

        # Create preview day
        day = DayEntity.create_for_date(
            date,
            user_id=user_id,
            template=template,
        )

        # Load preview tasks and existing data in parallel
        tasks, calendar_entries, messages = await asyncio.gather(
            self._preview_tasks_handler.preview_tasks(user_id, date),
            self._ro_repos.calendar_entry_ro_repo.search_query(value_objects.DateQuery(date=date)),
            self._ro_repos.message_ro_repo.search_query(value_objects.DateQuery(date=date)),
        )

        return value_objects.DayContext(
            day=day,
            tasks=tasks,
            calendar_entries=calendar_entries,
            messages=messages,
        )

    async def _get_template(
        self,
        user_id: UUID,
        date: date,
        template_id: UUID | None,
    ) -> DayTemplateEntity:
        """Get the template to use for the preview."""
        if template_id is not None:
            return await self._ro_repos.day_template_ro_repo.get(template_id)

        # Try to get from existing day
        try:
            day_id = DayEntity.id_from_date_and_user(date, user_id)
            existing_day = await self._ro_repos.day_ro_repo.get(day_id)
            if existing_day.template:
                return existing_day.template
        except NotFoundError:
            pass

        # Fall back to user's default template
        user = await self._ro_repos.user_ro_repo.get(user_id)
        template_slug = user.settings.template_defaults[date.weekday()]
        return await self._ro_repos.day_template_ro_repo.get_by_slug(template_slug)

