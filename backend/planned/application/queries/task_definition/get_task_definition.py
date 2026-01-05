"""Query to get a task definition by ID."""

from uuid import UUID

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from planned.domain.entities import TaskDefinitionEntity


class GetTaskDefinitionHandler(BaseQueryHandler):
    """Retrieves a single task definition by ID."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def run(
        self, task_definition_id: UUID
    ) -> TaskDefinitionEntity:
        """Get a single task definition by ID.

        Args:
            task_definition_id: The ID of the task definition to retrieve

        Returns:
            The task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        return await self.task_definition_ro_repo.get(task_definition_id)

