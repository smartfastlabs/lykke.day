"""Command to remove a brain dump item from a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class RemoveBrainDumpItemCommand(Command):
    """Command to remove a brain dump item from a day."""

    date: date
    item_id: UUID


class RemoveBrainDumpItemHandler(
    BaseCommandHandler[RemoveBrainDumpItemCommand, DayEntity]
):
    """Removes a brain dump item from a day."""

    async def handle(self, command: RemoveBrainDumpItemCommand) -> DayEntity:
        """Remove a brain dump item from a day."""
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            day.remove_brain_dump_item(command.item_id)

            return uow.add(day)
