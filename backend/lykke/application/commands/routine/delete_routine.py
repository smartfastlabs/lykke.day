"""Command to delete a routine."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteRoutineCommand(Command):
    """Command to delete a routine."""

    routine_id: UUID


class DeleteRoutineHandler(BaseCommandHandler[DeleteRoutineCommand, None]):
    """Deletes a routine."""

    async def handle(self, command: DeleteRoutineCommand) -> None:
        """Delete a routine.

        Args:
            command: The command containing the routine ID to delete.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(command.routine_id)
            await uow.delete(routine)
