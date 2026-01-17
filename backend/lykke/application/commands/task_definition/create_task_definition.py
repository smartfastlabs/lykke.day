"""Command to create a new task definition."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TaskDefinitionEntity


@dataclass(frozen=True)
class CreateTaskDefinitionCommand(Command):
    """Command to create a new task definition."""

    task_definition: TaskDefinitionEntity


class CreateTaskDefinitionHandler(BaseCommandHandler[CreateTaskDefinitionCommand, TaskDefinitionEntity]):
    """Creates a new task definition."""

    async def handle(self, command: CreateTaskDefinitionCommand) -> TaskDefinitionEntity:
        """Create a new task definition.

        Args:
            command: The command containing the task definition entity to create

        Returns:
            The created task definition entity
        """
        async with self.new_uow() as uow:
            await uow.create(command.task_definition)
            return command.task_definition
