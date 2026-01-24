"""Command to attach a task definition to a routine."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects import RoutineTask


@dataclass(frozen=True)
class AddRoutineTaskCommand(Command):
    """Command to add a routine task."""

    routine_id: UUID
    routine_task: RoutineTask


class AddRoutineTaskHandler(BaseCommandHandler[AddRoutineTaskCommand, RoutineEntity]):
    """Attach a RoutineTask to a routine."""

    async def handle(self, command: AddRoutineTaskCommand) -> RoutineEntity:
        """Attach a task to the routine.

        Args:
            command: The command containing the routine ID and task to attach.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(command.routine_id)
            updated = routine.add_task(command.routine_task)
            return uow.add(updated)
