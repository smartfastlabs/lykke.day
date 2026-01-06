"""Command to detach a task definition from a routine."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import RoutineEntity


class RemoveRoutineTaskHandler(BaseCommandHandler):
    """Detach a RoutineTask from a routine."""

    async def run(self, routine_id: UUID, task_definition_id: UUID) -> RoutineEntity:
        """Remove an attached task from the routine.

        Args:
            routine_id: ID of the routine.
            task_definition_id: ID of the task definition to detach.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            updated_routine = routine.remove_task(task_definition_id)
            uow.add(updated_routine)
            return updated_routine
