"""Command to detach a task definition from a routine."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineEntity


@dataclass(frozen=True)
class RemoveRoutineTaskCommand(Command):
    """Command to remove a routine task."""

    routine_id: UUID
    routine_task_id: UUID


class RemoveRoutineTaskHandler(BaseCommandHandler[RemoveRoutineTaskCommand, RoutineEntity]):
    """Detach a RoutineTask from a routine."""

    async def handle(self, command: RemoveRoutineTaskCommand) -> RoutineEntity:
        """Remove an attached task from the routine.

        Args:
            command: The command containing the routine ID and task ID to remove.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(command.routine_id)
            updated_routine = routine.remove_task(command.routine_task_id)
            return uow.add(updated_routine)
