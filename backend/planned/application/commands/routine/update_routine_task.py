"""Command to update an attached routine task."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.core.exceptions import NotFoundError
from planned.domain.entities import RoutineEntity
from planned.domain.value_objects import RoutineTask


class UpdateRoutineTaskHandler(BaseCommandHandler):
    """Update the metadata or schedule of an attached RoutineTask."""

    async def run(
        self,
        routine_id: UUID,
        task_update: RoutineTask,
    ) -> RoutineEntity:
        """Update an attached RoutineTask.

        Args:
            routine_id: ID of the routine to update.
            task_update: RoutineTask containing updates (matched by task_definition_id).

        Raises:
            NotFoundError: If the task_definition_id is not attached.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            tasks = routine.tasks or []

            updated_tasks: list[RoutineTask] = []
            found = False

            for task in tasks:
                if task.task_definition_id == task_update.task_definition_id:
                    updated_tasks.append(
                        RoutineTask(
                            task_definition_id=task.task_definition_id,
                            name=task_update.name if task_update.name is not None else task.name,
                            schedule=(
                                task_update.schedule
                                if task_update.schedule is not None
                                else task.schedule
                            ),
                        )
                    )
                    found = True
                else:
                    updated_tasks.append(task)

            if not found:
                raise NotFoundError("Routine task not found")

            updated_routine = routine.clone(tasks=updated_tasks)
            uow.add(updated_routine)
            return updated_routine

