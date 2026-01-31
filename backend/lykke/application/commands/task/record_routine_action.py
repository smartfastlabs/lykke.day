"""Command to record an action on all tasks in a routine for today."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


@dataclass(frozen=True)
class RecordRoutineActionCommand(Command):
    """Command to record an action on all tasks in a routine."""

    routine_id: UUID
    action: value_objects.Action


class RecordRoutineActionHandler(
    BaseCommandHandler[RecordRoutineActionCommand, list[TaskEntity]]
):
    """Records an action on all tasks in a routine for today."""

    async def handle(self, command: RecordRoutineActionCommand) -> list[TaskEntity]:
        """Record an action on all tasks in a routine for today.

        Args:
            command: The command containing the routine ID and action

        Returns:
            List of updated Task entities

        Raises:
            NotFoundError: If the routine or day is not found
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(command.routine_id)

            day_id = DayEntity.id_from_date_and_user(routine.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(
                    date=routine.date,
                    routine_definition_ids=[routine.routine_definition_id],
                )
            )

            # Only apply "punt" / "complete" to tasks that haven't already been
            # punted or completed.
            if command.action.type in (
                value_objects.ActionType.PUNT,
                value_objects.ActionType.COMPLETE,
            ):
                tasks = [
                    task
                    for task in tasks
                    if task.status
                    not in (
                        value_objects.TaskStatus.PUNT,
                        value_objects.TaskStatus.COMPLETE,
                    )
                ]

            updated_tasks: list[TaskEntity] = []
            for task in tasks:
                updated_task = day.record_task_action(task, command.action)
                updated_tasks.append(updated_task)

            uow.add(day)
            for task in updated_tasks:
                if task.has_events():
                    uow.add(task)

            return updated_tasks
