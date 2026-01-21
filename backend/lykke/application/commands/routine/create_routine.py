"""Command to create a new routine."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineEntity


@dataclass(frozen=True)
class CreateRoutineCommand(Command):
    """Command to create a new routine."""

    routine: RoutineEntity


class CreateRoutineHandler(BaseCommandHandler[CreateRoutineCommand, RoutineEntity]):
    """Creates a new routine."""

    async def handle(self, command: CreateRoutineCommand) -> RoutineEntity:
        """Create a new routine.

        Args:
            command: The command containing the routine entity to create.

        Returns:
            The created routine entity.
        """
        async with self.new_uow() as uow:
            return await uow.create(command.routine)


