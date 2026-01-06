"""Command to attach a task definition to a routine."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.core.exceptions import DomainError
from planned.domain.entities import RoutineEntity
from planned.domain.value_objects import RoutineTask


class AddRoutineTaskHandler(BaseCommandHandler):
    """Attach a RoutineTask to a routine."""

    async def run(self, routine_id: UUID, task: RoutineTask) -> RoutineEntity:
        """Attach a task to the routine if not already present.

        Args:
            routine_id: ID of the routine to update.
            task: RoutineTask to attach.

        Raises:
            DomainError: If the task_definition_id is already attached.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            existing_tasks = routine.tasks or []

            if any(t.task_definition_id == task.task_definition_id for t in existing_tasks):
                raise DomainError("Task definition already attached to routine")

            updated_tasks = [*existing_tasks, task]
            updated_routine = routine.clone(tasks=updated_tasks)

            uow.add(updated_routine)
            return updated_routine

