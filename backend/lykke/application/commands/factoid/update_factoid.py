"""Command to update an existing factoid."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import FactoidRepositoryReadOnlyProtocol
from lykke.domain.entities import FactoidEntity
from lykke.domain.events.ai_chat_events import FactoidUpdatedEvent
from lykke.domain.value_objects import FactoidUpdateObject


@dataclass(frozen=True)
class UpdateFactoidCommand(Command):
    """Command to update an existing factoid."""

    factoid_id: UUID
    update_data: FactoidUpdateObject


class UpdateFactoidHandler(BaseCommandHandler[UpdateFactoidCommand, FactoidEntity]):
    """Updates an existing factoid."""

    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol

    async def handle(self, command: UpdateFactoidCommand) -> FactoidEntity:
        """Update an existing factoid.

        Args:
            command: The command containing the factoid ID and update data

        Returns:
            The updated factoid entity

        Raises:
            NotFoundError: If factoid not found
        """
        async with self.new_uow() as uow:
            factoid = await self.factoid_ro_repo.get(command.factoid_id)
            factoid = factoid.apply_update(command.update_data, FactoidUpdatedEvent)
            return uow.add(factoid)
