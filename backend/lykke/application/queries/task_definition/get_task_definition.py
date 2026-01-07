"""Query to get a task definition by ID."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from lykke.infrastructure import data_objects


class GetTaskDefinitionHandler(BaseQueryHandler):
    """Retrieves a single task definition by ID."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def run(
        self, task_definition_id: UUID
    ) -> data_objects.TaskDefinition:
        """Get a single task definition by ID.

        Args:
            task_definition_id: The ID of the task definition to retrieve

        Returns:
            The task definition data object

        Raises:
            NotFoundError: If task definition not found
        """
        return await self.task_definition_ro_repo.get(task_definition_id)

