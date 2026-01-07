"""Command to update an attached routine task."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects import RoutineTask


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
            task_update: RoutineTask containing updates (matched by RoutineTask.id).

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            updated_routine = routine.update_task(task_update)
            uow.add(updated_routine)
            return updated_routine
