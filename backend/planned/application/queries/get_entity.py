"""Generic query to get a single entity by ID."""

from typing import TypeVar
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory

EntityT = TypeVar("EntityT")


class GetEntityHandler:
    """Retrieves a single entity by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_entity(
        self, user_id: UUID, repository_name: str, entity_id: UUID
    ) -> EntityT:
        """Get a single entity by ID.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            entity_id: The ID of the entity to retrieve

        Returns:
            The entity

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)
            result: EntityT = await repo.get(entity_id)
            return result
