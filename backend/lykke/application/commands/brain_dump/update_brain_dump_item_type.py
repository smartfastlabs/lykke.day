"""Command to update a brain dump item's type."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects


@dataclass(frozen=True)
class UpdateBrainDumpItemTypeCommand(Command):
    """Command to update a brain dump item's type."""

    date: dt_date
    item_id: UUID
    item_type: value_objects.BrainDumpItemType


class UpdateBrainDumpItemTypeHandler(
    BaseCommandHandler[UpdateBrainDumpItemTypeCommand, None]
):
    """Updates a brain dump item's type."""

    async def handle(self, command: UpdateBrainDumpItemTypeCommand) -> None:
        """Update a brain dump item's type."""
        async with self.new_uow() as uow:
            item = await uow.brain_dump_ro_repo.get(command.item_id)
            if item.date != command.date:
                raise DomainError(
                    f"Brain dump item {command.item_id} not found for {command.date}"
                )

            updated = item.update_type(command.item_type)
            if updated.has_events():
                uow.add(updated)
