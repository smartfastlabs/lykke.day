"""Command to update an existing routine."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineEntity
from lykke.domain.events.routine import RoutineUpdatedEvent
from lykke.domain.value_objects import RoutineUpdateObject


@dataclass(frozen=True)
class UpdateRoutineCommand(Command):
    """Command to update an existing routine."""

    routine_id: UUID
    update_data: RoutineUpdateObject


class UpdateRoutineHandler(BaseCommandHandler[UpdateRoutineCommand, RoutineEntity]):
    """Updates an existing routine."""

    async def handle(self, command: UpdateRoutineCommand) -> RoutineEntity:
        """Update an existing routine.

        Args:
            command: The command containing the routine ID and update data.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            # Get the existing routine
            routine = await uow.routine_ro_repo.get(command.routine_id)

            # Apply updates using domain method (adds RoutineUpdatedEvent)
            routine = routine.apply_update(command.update_data, RoutineUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(routine)
            return routine
