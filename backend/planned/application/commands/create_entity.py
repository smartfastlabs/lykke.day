"""Generic command to create a new entity."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from planned.application.commands.base import Command, CommandHandler
from planned.application.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class CreateEntityCommand(Command):
    """Command to create a new entity.

    Attributes:
        user_id: The user making the request
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
        entity: The entity to create
    """

    user_id: UUID
    repository_name: str
    entity: Any


class CreateEntityHandler(CommandHandler[CreateEntityCommand, Any]):
    """Handles CreateEntityCommand - creates a new entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: CreateEntityCommand) -> Any:
        """Execute the command.

        Args:
            command: The create command

        Returns:
            The created entity
        """
        async with self._uow_factory.create(command.user_id) as uow:
            repo = getattr(uow, command.repository_name)
            entity = await repo.put(command.entity)
            await uow.commit()
            return entity

