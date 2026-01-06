"""Command to attach a task definition to a routine."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import RoutineEntity
from planned.domain.value_objects import RoutineTask


class AddRoutineTaskHandler(BaseCommandHandler):
    """Attach a RoutineTask to a routine."""

    async def run(self, routine_id: UUID, task: RoutineTask) -> RoutineEntity:
        """Attach a task to the routine.

        Args:
            routine_id: ID of the routine to update.
            task: RoutineTask to attach.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            updated = routine.add_task(task)
            uow.add(updated)
            return updated

