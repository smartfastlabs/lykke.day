"""Query to get a routine by ID."""

from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import RoutineRepositoryReadOnlyProtocol
from lykke.domain.entities import RoutineEntity


class GetRoutineHandler(BaseQueryHandler):
    """Retrieves a single routine by ID."""

    routine_ro_repo: RoutineRepositoryReadOnlyProtocol

    async def run(self, routine_id: UUID) -> RoutineEntity:
        """Get a single routine by ID.

        Args:
            routine_id: The ID of the routine to retrieve

        Returns:
            The routine entity

        Raises:
            NotFoundError: If routine not found
        """
        return await self.routine_ro_repo.get(routine_id)

