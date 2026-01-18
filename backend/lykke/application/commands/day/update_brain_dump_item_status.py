"""Command to update a brain dump item's status on a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class UpdateBrainDumpItemStatusCommand(Command):
    """Command to update a brain dump item's status on a day."""

    date: date
    item_id: UUID
    status: value_objects.BrainDumpItemStatus


class UpdateBrainDumpItemStatusHandler(
    BaseCommandHandler[UpdateBrainDumpItemStatusCommand, DayEntity]
):
    """Updates a brain dump item's status on a day."""

    async def handle(
        self, command: UpdateBrainDumpItemStatusCommand
    ) -> DayEntity:
        """Update a brain dump item's status on a day."""
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            day.update_brain_dump_item_status(command.item_id, command.status)

            if day.has_events():
                uow.add(day)
            return day
