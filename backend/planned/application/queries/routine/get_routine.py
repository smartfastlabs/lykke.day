"""Query to get a routine by ID."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain.entities import RoutineEntity


class GetRoutineHandler:
    """Retrieves a single routine by ID."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

    async def run(self, routine_id: UUID) -> RoutineEntity:
        """Get a single routine by ID.

        Args:
            routine_id: The ID of the routine to retrieve

        Returns:
            The routine entity

        Raises:
            NotFoundError: If routine not found
        """
        return await self._ro_repos.routine_ro_repo.get(routine_id)

