"""Generic command to delete an entity."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteEntityHandler:
    """Deletes an entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def delete_entity(
        self, user_id: UUID, repository_name: str, entity_id: UUID
    ) -> None:
        """Delete an entity.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            entity_id: The ID of the entity to delete

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)
            entity = await repo.get(entity_id)
            await repo.delete(entity)
            await uow.commit()

