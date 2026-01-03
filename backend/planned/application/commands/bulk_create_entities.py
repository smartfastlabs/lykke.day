"""Generic command to bulk create entities."""

from typing import TypeVar
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory

EntityT = TypeVar("EntityT")


class BulkCreateEntitiesHandler:
    """Creates multiple entities."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def bulk_create_entities(
        self, user_id: UUID, repository_name: str, entities: tuple[EntityT, ...]
    ) -> list[EntityT]:
        """Create multiple entities.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            entities: Tuple of entities to create

        Returns:
            List of created entities
        """
        if not entities:
            return []

        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)
            created: list[EntityT] = await repo.insert_many(*entities)
            await uow.commit()
            return created
