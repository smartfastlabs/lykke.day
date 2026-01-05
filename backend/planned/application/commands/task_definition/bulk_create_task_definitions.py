"""Command to bulk create task definitions."""

from planned.application.commands.base import BaseCommandHandler
from planned.infrastructure import data_objects


class BulkCreateTaskDefinitionsHandler(BaseCommandHandler):
    """Creates multiple task definitions."""

    async def run(
        self, task_definitions: tuple[data_objects.TaskDefinition, ...]
    ) -> list[data_objects.TaskDefinition]:
        """Create multiple task definitions.

        Args:
            task_definitions: Tuple of task definition data objects to create

        Returns:
            List of created task definition data objects
        """
        if not task_definitions:
            return []

        async with self.new_uow() as uow:
            # Create each task definition
            for task_definition in task_definitions:
                await uow.create(task_definition)
            return list(task_definitions)

