"""Generic command to bulk create entities."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from planned.application.commands.base import Command, CommandHandler
from planned.application.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class BulkCreateEntitiesCommand(Command):
    """Command to create multiple entities.

    Attributes:
        user_id: The user making the request
        repository_name: Name of the repository on UoW (e.g., "days", "tasks")
        entities: List of entities to create
    """

    user_id: UUID
    repository_name: str
    entities: tuple[Any, ...]  # Use tuple for frozen dataclass


class BulkCreateEntitiesHandler(CommandHandler[BulkCreateEntitiesCommand, list[Any]]):
    """Handles BulkCreateEntitiesCommand - creates multiple entities."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: BulkCreateEntitiesCommand) -> list[Any]:
        """Execute the command.

        Args:
            command: The bulk create command

        Returns:
            List of created entities
        """
        if not command.entities:
            return []

        async with self._uow_factory.create(command.user_id) as uow:
            repo = getattr(uow, command.repository_name)
            created = await repo.insert_many(*command.entities)
            await uow.commit()
            return created  # type: ignore[no-any-return]

