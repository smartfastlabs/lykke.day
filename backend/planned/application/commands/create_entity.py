"""Generic command to create a new entity."""

from typing import TypeVar
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory

EntityT = TypeVar("EntityT")


class CreateEntityHandler:
    """Creates a new entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create_entity(
        self, user_id: UUID, repository_name: str, entity: EntityT
    ) -> EntityT:
        """Create a new entity.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            entity: The entity to create

        Returns:
            The created entity
        """
        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)
            created_entity: EntityT = await repo.put(entity)
            await uow.commit()
            return created_entity
