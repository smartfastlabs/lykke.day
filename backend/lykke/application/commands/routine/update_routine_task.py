"""Command to update an attached routine task."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineEntity
from lykke.domain.value_objects import RoutineTask


@dataclass(frozen=True)
class UpdateRoutineTaskCommand(Command):
    """Command to update a routine task."""

    routine_id: UUID
    routine_task_id: UUID
    routine_task: RoutineTask


class UpdateRoutineTaskHandler(
    BaseCommandHandler[UpdateRoutineTaskCommand, RoutineEntity]
):
    """Update the metadata or schedule of an attached RoutineTask."""

    async def handle(self, command: UpdateRoutineTaskCommand) -> RoutineEntity:
        """Update an attached RoutineTask.

        Args:
            command: The command containing the routine ID, task ID, and task updates.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            routine = await uow.routine_ro_repo.get(command.routine_id)
            updated_routine = routine.update_task(command.routine_task)
            return uow.add(updated_routine)
