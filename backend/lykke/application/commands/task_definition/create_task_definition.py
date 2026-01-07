"""Command to create a new task definition."""

from lykke.application.commands.base import BaseCommandHandler
from lykke.infrastructure import data_objects


class CreateTaskDefinitionHandler(BaseCommandHandler):
    """Creates a new task definition."""

    async def run(self, task_definition: data_objects.TaskDefinition) -> data_objects.TaskDefinition:
        """Create a new task definition.

        Args:
            task_definition: The task definition data object to create

        Returns:
            The created task definition data object
        """
        async with self.new_uow() as uow:
            await uow.create(task_definition)
            return task_definition
