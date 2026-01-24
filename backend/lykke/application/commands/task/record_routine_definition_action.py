"""Command to record an action on all tasks in a routine definition for today."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


@dataclass(frozen=True)
class RecordRoutineDefinitionActionCommand(Command):
    """Command to record an action on all tasks in a routine definition."""

    routine_definition_id: UUID
    action: value_objects.Action
    date: date


class RecordRoutineDefinitionActionHandler(
    BaseCommandHandler[RecordRoutineDefinitionActionCommand, list[TaskEntity]]
):
    """Records an action on all tasks in a routine definition for today."""

    async def handle(
        self, command: RecordRoutineDefinitionActionCommand
    ) -> list[TaskEntity]:
        """Record an action on all tasks in a routine definition for today.

        Args:
            command: The command containing the routine definition ID, action, and date

        Returns:
            List of updated Task entities

        Raises:
            NotFoundError: If the day is not found
        """
        async with self.new_uow() as uow:
            # Get the Day aggregate root
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Find all tasks for this routine definition on today's date
            tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(
                    date=command.date,
                    routine_definition_ids=[command.routine_definition_id],
                )
            )

            # Record the action on each task
            updated_tasks: list[TaskEntity] = []
            for task in tasks:
                updated_task = day.record_task_action(task, command.action)
                updated_tasks.append(updated_task)

            # Add both Day (for events) and Tasks (for state changes) to UoW
            uow.add(day)
            for task in updated_tasks:
                uow.add(task)

            return updated_tasks
