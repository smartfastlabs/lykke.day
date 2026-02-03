"""Command to delete a brain dump."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.core.exceptions import DomainError
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class DeleteBrainDumpCommand(Command):
    """Command to delete a brain dump."""

    date: dt_date
    item_id: UUID


class DeleteBrainDumpHandler(BaseCommandHandler[DeleteBrainDumpCommand, BrainDumpEntity]):
    """Deletes a brain dump."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteBrainDumpCommand) -> BrainDumpEntity:
        """Delete a brain dump."""
        async with self.new_uow() as uow:
            item = await self.brain_dump_ro_repo.get(command.item_id)
            if item.date != command.date:
                raise DomainError(
                    f"Brain dump {command.item_id} not found for {command.date}"
                )

            item.mark_removed()
            await uow.delete(item)
            return item
