"""Command to delete a task definition."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteTaskDefinitionHandler:
    """Deletes a task definition."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self, task_definition_id: UUID
    ) -> None:
        """Delete a task definition.

        Args:
            task_definition_id: The ID of the task definition to delete

        Raises:
            NotFoundError: If task definition not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            task_definition = await uow.task_definition_ro_repo.get(task_definition_id)
            task_definition.delete()  # Mark for deletion
            uow.add(task_definition)

