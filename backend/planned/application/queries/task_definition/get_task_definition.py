"""Query to get a task definition by ID."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain.entities import TaskDefinitionEntity


class GetTaskDefinitionHandler:
    """Retrieves a single task definition by ID."""

    def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
        self._ro_repos = ro_repos

    async def run(
        self, user_id: UUID, task_definition_id: UUID
    ) -> TaskDefinitionEntity:
        """Get a single task definition by ID.

        Args:
            user_id: The user making the request
            task_definition_id: The ID of the task definition to retrieve

        Returns:
            The task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        return await self._ro_repos.task_definition_ro_repo.get(task_definition_id)

