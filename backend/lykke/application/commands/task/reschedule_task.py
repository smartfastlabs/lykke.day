"""Command to reschedule a task to a new date."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TaskEntity


@dataclass(frozen=True)
class RescheduleTaskCommand(Command):
    """Command to change the scheduled date of a task."""

    task_id: UUID
    scheduled_date: dt_date


class RescheduleTaskHandler(BaseCommandHandler[RescheduleTaskCommand, TaskEntity]):
    """Reschedules a task to a new date."""

    async def handle(self, command: RescheduleTaskCommand) -> TaskEntity:
        async with self.new_uow() as uow:
            task = await uow.task_ro_repo.get(command.task_id)

            if task.scheduled_date == command.scheduled_date:
                return task

            updated_task = task.reschedule(command.scheduled_date)
            uow.add(updated_task)

            return updated_task
