"""Generic command to update an existing entity."""

from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from planned.application.commands.base import Command, CommandHandler
from planned.application.unit_of_work import UnitOfWorkFactory

EntityT = TypeVar("EntityT")


@dataclass(frozen=True)
class UpdateEntityCommand(Command, Generic[EntityT]):
    """Command to update an existing entity.

    Attributes:
        user_id: The user making the request
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
        entity_id: The ID of the entity to update
        entity_data: The updated entity data
    """

    user_id: UUID
    repository_name: str
    entity_id: UUID
    entity_data: EntityT


class UpdateEntityHandler(CommandHandler[UpdateEntityCommand[EntityT], EntityT]):
    """Handles UpdateEntityCommand - updates an existing entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: UpdateEntityCommand[EntityT]) -> EntityT:
        """Execute the command.

        Args:
            command: The update command

        Returns:
            The updated entity

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(command.user_id) as uow:
            repo = getattr(uow, command.repository_name)

            # Get existing entity
            existing: EntityT = await repo.get(command.entity_id)

            # Merge updates
            if hasattr(existing, "model_copy") and hasattr(
                command.entity_data, "model_dump"
            ):
                updated = existing.model_copy(
                    update=command.entity_data.model_dump(exclude_unset=True)
                )
            else:
                updated = command.entity_data

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", command.entity_id)

            entity: EntityT = await repo.put(updated)
            await uow.commit()
            return entity
