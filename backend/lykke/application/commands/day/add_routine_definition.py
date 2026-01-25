"""Command to add a routine definition's tasks to a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, RoutineEntity, TaskEntity


@dataclass(frozen=True)
class AddRoutineDefinitionToDayCommand(Command):
    """Command to add a routine definition's tasks to a day."""

    date: date
    routine_definition_id: UUID


class AddRoutineDefinitionToDayHandler(
    BaseCommandHandler[AddRoutineDefinitionToDayCommand, list[TaskEntity]]
):
    """Adds a routine definition's tasks to a day."""

    async def handle(
        self, command: AddRoutineDefinitionToDayCommand
    ) -> list[TaskEntity]:
        """Add all tasks from a routine definition to a day.

        Args:
            command: The command containing the date and routine definition ID

        Returns:
            The created tasks (or existing tasks if already added)
        """
        async with self.new_uow() as uow:
            # Ensure day exists for the given date
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            await uow.day_ro_repo.get(day_id)

            routine_definition = await uow.routine_definition_ro_repo.get(
                command.routine_definition_id
            )

            existing_routines = await uow.routine_ro_repo.search(
                value_objects.RoutineQuery(
                    date=command.date,
                    routine_definition_ids=[command.routine_definition_id],
                )
            )
            if not existing_routines:
                routine = RoutineEntity(
                    user_id=self.user_id,
                    date=command.date,
                    routine_definition_id=routine_definition.id,
                    name=routine_definition.name,
                    category=routine_definition.category,
                    description=routine_definition.description,
                    time_window=routine_definition.time_window,
                )
                await uow.create(routine)

            existing_tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(
                    date=command.date,
                    routine_definition_ids=[command.routine_definition_id],
                )
            )
            if existing_tasks:
                return existing_tasks

            created_tasks: list[TaskEntity] = []
            for routine_definition_task in routine_definition.tasks:
                task_definition = await uow.task_definition_ro_repo.get(
                    routine_definition_task.task_definition_id
                )
                task = TaskEntity(
                    user_id=self.user_id,
                    scheduled_date=command.date,
                    name=(
                        routine_definition_task.name
                        or f"ROUTINE DEFINITION: {routine_definition.name}"
                    ),
                    status=value_objects.TaskStatus.NOT_STARTED,
                    type=task_definition.type,
                    description=task_definition.description,
                    category=routine_definition.category,
                    frequency=routine_definition.routine_definition_schedule.frequency,
                    schedule=routine_definition_task.schedule,
                    routine_definition_id=routine_definition.id,
                )
                created = await uow.create(task)
                created_tasks.append(created)

            return created_tasks
