"""Command to reschedule a day - clean up and recreate tasks."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.day.schedule_day import (
    ScheduleDayCommand,
    ScheduleDayHandler,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class RescheduleDayCommand(Command):
    """Command to reschedule a day."""

    date: dt_date
    template_id: UUID | None = None


class RescheduleDayHandler(
    BaseCommandHandler[RescheduleDayCommand, value_objects.DayContext]
):
    """Reschedules a day by cleaning up existing tasks and audit logs, then creating fresh tasks."""

    schedule_day_handler: ScheduleDayHandler

    async def handle(self, command: RescheduleDayCommand) -> value_objects.DayContext:
        """Reschedule a day by cleaning up and recreating all tasks.

        This operation:
        1. Deletes all existing tasks for the date
        2. Deletes all audit logs for the date
        3. Gets or creates the Day entity
        4. Schedules the day with fresh tasks from routines

        Args:
            command: The command containing the date and optional template ID

        Returns:
            A DayContext with the rescheduled day and tasks
        """
        logger.info(f"Rescheduling day for {command.date}")

        async with self.new_uow() as uow:
            # Step 1: Get the existing Day entity
            day_id = DayEntity.id_from_date_and_user(command.date, self.user.id)
            day = await uow.day_ro_repo.get(day_id)
            logger.info(f"Found existing day for {command.date}")

            # Step 2: Delete all existing tasks for this date
            # First, verify how many tasks exist before deletion for logging
            existing_tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(date=command.date, is_adhoc=False)
            )
            logger.info(
                f"Found {len(existing_tasks)} existing tasks for {command.date}, deleting..."
            )

            await uow.bulk_delete_tasks(
                value_objects.TaskQuery(date=command.date, is_adhoc=False)
            )

            # Verify deletion worked
            remaining_tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(date=command.date, is_adhoc=False)
            )
            if remaining_tasks:
                logger.warning(
                    f"Warning: {len(remaining_tasks)} tasks still exist after deletion. "
                    f"Task IDs: {[t.id for t in remaining_tasks]}"
                )
                # Force delete any remaining tasks individually as a safeguard
                for task in remaining_tasks:
                    await uow.delete(task)
                logger.info(f"Force deleted {len(remaining_tasks)} remaining tasks")

            # Step 3: Delete all audit logs for this date
            # Note: Audit logs are normally immutable, but reschedule is a special case
            # where we want a clean slate
            logger.info(f"Deleting audit logs for {command.date}")
            await uow.bulk_delete_audit_logs(
                value_objects.AuditLogQuery(date=command.date)
            )

            # Step 4: Reuse ScheduleDay logic to rebuild template, time blocks, and tasks
            day_context = await self.schedule_day_handler.schedule_day_in_uow(
                uow,
                ScheduleDayCommand(date=command.date, template_id=command.template_id),
                existing_day=day,
                force=True,
                cleanup_existing_tasks=False,
            )

            logger.info(f"Successfully rescheduled day for {command.date}")

            return day_context
