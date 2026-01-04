"""Command to schedule a day with tasks from routines."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.queries.preview_day import PreviewDayHandler
from planned.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from planned.domain import value_objects
from planned.domain.entities import DayEntity


class ScheduleDayHandler:
    """Schedules a day with tasks from routines."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        ro_repo_factory: ReadOnlyRepositoryFactory,
        user_id: UUID,
    ) -> None:
        self._uow_factory = uow_factory
        self._ro_repo_factory = ro_repo_factory
        self.user_id = user_id

    def _get_preview_handler(self) -> PreviewDayHandler:
        """Create a PreviewDayHandler with read-only repositories for the user."""
        ro_repos = self._ro_repo_factory.create(self.user_id)
        return PreviewDayHandler(ro_repos, self.user_id)

    async def schedule_day(
        self, date: date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            date: The date to schedule
            template_id: Optional template ID to use

        Returns:
            A DayContext with the scheduled day and tasks
        """
        async with self._uow_factory.create(self.user_id) as uow:
            # Delete existing tasks for this date
            await uow.task_rw_repo.delete_many(value_objects.DateQuery(date=date))

            # Get preview of what the day would look like
            preview_handler = self._get_preview_handler()
            preview_result = await preview_handler.preview_day(
                date, template_id
            )

            # Validate template exists
            if preview_result.day.template is None:
                raise ValueError("Day template is required to schedule")

            # Re-fetch template to ensure it's in the current UoW context
            template = await uow.day_template_rw_repo.get(preview_result.day.template.id)

            # Create and schedule the day
            day = DayEntity.create_for_date(
                date,
                user_id=self.user_id,
                template=template,
            )
            day.schedule(template)

            # Get tasks from preview
            tasks = preview_result.tasks

            # Save day and tasks
            await asyncio.gather(
                uow.day_rw_repo.put(day),
                *[uow.task_rw_repo.put(task) for task in tasks],
            )
            await uow.commit()

            return value_objects.DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=preview_result.calendar_entries,
                messages=preview_result.messages,
            )

