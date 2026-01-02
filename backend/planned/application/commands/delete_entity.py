"""Generic command to delete an entity."""

from dataclasses import dataclass
from uuid import UUID

from planned.application.commands.base import Command, CommandHandler
from planned.application.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class DeleteEntityCommand(Command):
    """Command to delete an entity.

    Attributes:
        user_id: The user making the request
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
        entity_id: The ID of the entity to delete
    """

    user_id: UUID
    repository_name: str
    entity_id: UUID


class DeleteEntityHandler(CommandHandler[DeleteEntityCommand, None]):
    """Handles DeleteEntityCommand - deletes an entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: DeleteEntityCommand) -> None:
        """Execute the command.

        Args:
            command: The delete command

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(command.user_id) as uow:
            repo = getattr(uow, command.repository_name)
            entity = await repo.get(command.entity_id)
            await repo.delete(entity)
            await uow.commit()

