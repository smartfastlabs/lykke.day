"""Query to get a routine by ID."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import RoutineEntity


class GetRoutineHandler:
    """Retrieves a single routine by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(self, user_id: UUID, routine_id: UUID) -> RoutineEntity:
        """Get a single routine by ID.

        Args:
            user_id: The user making the request
            routine_id: The ID of the routine to retrieve

        Returns:
            The routine entity

        Raises:
            NotFoundError: If routine not found
        """
        async with self._uow_factory.create(user_id) as uow:
            return await uow.routines.get(routine_id)

