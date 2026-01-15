"""Command to reschedule a day - clean up and recreate tasks."""

from datetime import date as dt_date
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.queries.preview_day import PreviewDayHandler
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class RescheduleDayHandler(BaseCommandHandler):
    """Reschedules a day by cleaning up existing tasks and audit logs, then creating fresh tasks."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        preview_day_handler: PreviewDayHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self.preview_day_handler = preview_day_handler

    async def reschedule_day(
        self, date: dt_date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Reschedule a day by cleaning up and recreating all tasks.

        This operation:
        1. Deletes all existing tasks for the date
        2. Deletes all audit logs for the date
        3. Gets or creates the Day entity
        4. Schedules the day with fresh tasks from routines

        Args:
            date: The date to reschedule
            template_id: Optional template ID to use

        Returns:
            A DayContext with the rescheduled day and tasks
        """
        logger.info(f"Rescheduling day for {date}")
        
        async with self.new_uow() as uow:
            # Step 1: Delete all existing tasks for this date
            logger.info(f"Deleting existing tasks for {date}")
            await uow.bulk_delete_tasks(value_objects.TaskQuery(date=date))

            # Step 2: Delete all audit logs for this date
            # Note: Audit logs are normally immutable, but reschedule is a special case
            # where we want a clean slate
            logger.info(f"Deleting audit logs for {date}")
            await uow.bulk_delete_audit_logs(value_objects.AuditLogQuery(date=date))

            # Step 3: Get or create the Day entity
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                day = await uow.day_ro_repo.get(day_id)
                logger.info(f"Found existing day for {date}")
            except Exception:
                # Day doesn't exist, create it
                logger.info(f"Creating new day for {date}")
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.search_one(
                    value_objects.DayTemplateQuery(slug=template_slug)
                )
                day = DayEntity.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                )
                await uow.create(day)

            # Step 4: Get preview of what tasks should be created
            preview_result = await self.preview_day_handler.preview_day(
                date, template_id
            )

            # Validate template exists
            if preview_result.day.template is None:
                raise ValueError("Day template is required to reschedule")

            # Re-fetch template to ensure it's in the current UoW context
            template = await uow.day_template_ro_repo.get(
                preview_result.day.template.id
            )

            # Schedule the day if it's not already scheduled
            if day.status == value_objects.DayStatus.UNSCHEDULED:
                day.schedule(template)
                uow.add(day)

            # Step 5: Create fresh tasks from preview
            logger.info(f"Creating {len(preview_result.tasks)} tasks for {date}")
            tasks = preview_result.tasks
            for task in tasks:
                await uow.create(task)

            logger.info(f"Successfully rescheduled day for {date}")
            
            return value_objects.DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=preview_result.calendar_entries,
            )
