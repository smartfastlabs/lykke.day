"""Command to create a new task definition."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import TaskDefinitionEntity


class CreateTaskDefinitionHandler(BaseCommandHandler):
    """Creates a new task definition."""

    async def run(self, task_definition: TaskDefinitionEntity) -> TaskDefinitionEntity:
        """Create a new task definition.

        Args:
            task_definition: The task definition entity to create

        Returns:
            The created task definition entity
        """
        async with self.new_uow() as uow:
            await uow.create(task_definition)
            return task_definition
