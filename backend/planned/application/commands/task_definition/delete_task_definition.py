"""Command to delete a task definition."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler


class DeleteTaskDefinitionHandler(BaseCommandHandler):
    """Deletes a task definition."""

    async def run(
        self, task_definition_id: UUID
    ) -> None:
        """Delete a task definition.

        Args:
            task_definition_id: The ID of the task definition to delete

        Raises:
            NotFoundError: If task definition not found
        """
        async with self.new_uow() as uow:
            task_definition = await uow.task_definition_ro_repo.get(task_definition_id)
            await uow.delete(task_definition)

