"""Command to update a brain dump item's status."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class UpdateBrainDumpItemStatusCommand(Command):
    """Command to update a brain dump item's status."""

    date: dt_date
    item_id: UUID
    status: value_objects.BrainDumpItemStatus


class UpdateBrainDumpItemStatusHandler(
    BaseCommandHandler[UpdateBrainDumpItemStatusCommand, BrainDumpEntity]
):
    """Updates a brain dump item's status."""

    async def handle(
        self, command: UpdateBrainDumpItemStatusCommand
    ) -> BrainDumpEntity:
        """Update a brain dump item's status."""
        async with self.new_uow() as uow:
            item = await uow.brain_dump_ro_repo.get(command.item_id)
            if item.date != command.date:
                raise DomainError(
                    f"Brain dump item {command.item_id} not found for {command.date}"
                )

            updated = item.update_status(command.status)
            if updated.has_events():
                uow.add(updated)
            return updated
