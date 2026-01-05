"""Command to schedule a day with tasks from routines."""

from datetime import date
from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.application.queries.preview_day import PreviewDayHandler
from planned.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from planned.domain import value_objects
from planned.domain.entities import DayEntity


class ScheduleDayHandler(BaseCommandHandler):
    """Schedules a day with tasks from routines."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        preview_day_handler: PreviewDayHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self.preview_day_handler = preview_day_handler

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
        async with self.new_uow() as uow:
            # Delete existing tasks for this date
            # Get all tasks for the date and mark them for deletion
            existing_tasks = await uow.task_ro_repo.search_query(
                value_objects.DateQuery(date=date)
            )
            for task in existing_tasks:
                await uow.delete(task)

            # Get preview of what the day would look like
            preview_result = await self.preview_day_handler.preview_day(
                date, template_id
            )

            # Validate template exists
            if preview_result.day.template is None:
                raise ValueError("Day template is required to schedule")

            # Re-fetch template to ensure it's in the current UoW context
            template = await uow.day_template_ro_repo.get(
                preview_result.day.template.id
            )

            # Create and schedule the day
            day = DayEntity.create_for_date(
                date,
                user_id=self.user_id,
                template=template,
            )
            day.schedule(template)
            await uow.create(day)

            # Get tasks from preview and create them
            tasks = preview_result.tasks
            for task in tasks:
                await uow.create(task)

            return value_objects.DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=preview_result.calendar_entries,
            )
