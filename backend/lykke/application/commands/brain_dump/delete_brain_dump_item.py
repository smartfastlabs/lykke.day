"""Command to delete a brain dump item."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import DomainError
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class DeleteBrainDumpItemCommand(Command):
    """Command to delete a brain dump item."""

    date: dt_date
    item_id: UUID


class DeleteBrainDumpItemHandler(
    BaseCommandHandler[DeleteBrainDumpItemCommand, BrainDumpEntity]
):
    """Deletes a brain dump item."""

    async def handle(self, command: DeleteBrainDumpItemCommand) -> BrainDumpEntity:
        """Delete a brain dump item."""
        async with self.new_uow() as uow:
            item = await uow.brain_dump_ro_repo.get(command.item_id)
            if item.date != command.date:
                raise DomainError(
                    f"Brain dump item {command.item_id} not found for {command.date}"
                )

            item.mark_removed()
            await uow.delete(item)
            return item
