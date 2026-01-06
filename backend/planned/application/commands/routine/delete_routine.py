"""Command to delete a routine."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler


class DeleteRoutineHandler(BaseCommandHandler):
    """Deletes a routine."""

    async def run(self, routine_id: UUID) -> None:
        """Delete a routine.

        Args:
            routine_id: The ID of the routine to delete.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(routine_id)
            await uow.delete(routine)


