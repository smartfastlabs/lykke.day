"""Command to create a new routine definition."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineDefinitionEntity


@dataclass(frozen=True)
class CreateRoutineDefinitionCommand(Command):
    """Command to create a new routine definition."""

    routine_definition: RoutineDefinitionEntity


class CreateRoutineDefinitionHandler(
    BaseCommandHandler[CreateRoutineDefinitionCommand, RoutineDefinitionEntity]
):
    """Creates a new routine definition."""

    async def handle(
        self, command: CreateRoutineDefinitionCommand
    ) -> RoutineDefinitionEntity:
        """Create a new routine definition.

        Args:
            command: The command containing the routine definition entity to create.

        Returns:
            The created routine definition entity.
        """
        async with self.new_uow() as uow:
            return await uow.create(command.routine_definition)
