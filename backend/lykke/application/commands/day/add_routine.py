"""Command to add a routine's tasks to a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


@dataclass(frozen=True)
class AddRoutineToDayCommand(Command):
    """Command to add a routine's tasks to a day."""

    date: date
    routine_id: UUID


class AddRoutineToDayHandler(
    BaseCommandHandler[AddRoutineToDayCommand, list[TaskEntity]]
):
    """Adds a routine's tasks to a day."""

    async def handle(self, command: AddRoutineToDayCommand) -> list[TaskEntity]:
        """Add all tasks from a routine to a day.

        Args:
            command: The command containing the date and routine ID

        Returns:
            The created tasks (or existing tasks if already added)
        """
        async with self.new_uow() as uow:
            # Ensure day exists for the given date
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            await uow.day_ro_repo.get(day_id)

            routine = await uow.routine_ro_repo.get(command.routine_id)

            existing_tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(
                    date=command.date, routine_ids=[command.routine_id]
                )
            )
            if existing_tasks:
                return existing_tasks

            created_tasks: list[TaskEntity] = []
            for routine_task in routine.tasks:
                task_definition = await uow.task_definition_ro_repo.get(
                    routine_task.task_definition_id
                )
                task = TaskEntity(
                    user_id=self.user_id,
                    scheduled_date=command.date,
                    name=routine_task.name or f"ROUTINE: {routine.name}",
                    status=value_objects.TaskStatus.NOT_STARTED,
                    type=task_definition.type,
                    description=task_definition.description,
                    category=routine.category,
                    frequency=routine.routine_schedule.frequency,
                    schedule=routine_task.schedule,
                    routine_id=routine.id,
                )
                created = await uow.create(task)
                created_tasks.append(created)

            return created_tasks
