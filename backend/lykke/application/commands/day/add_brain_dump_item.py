"""Command to add a brain dump item to a day."""

from dataclasses import dataclass
from datetime import date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class AddBrainDumpItemToDayCommand(Command):
    """Command to add a brain dump item to a day."""

    date: date
    text: str


class AddBrainDumpItemToDayHandler(
    BaseCommandHandler[AddBrainDumpItemToDayCommand, DayEntity]
):
    """Adds a brain dump item to a day."""

    async def handle(self, command: AddBrainDumpItemToDayCommand) -> DayEntity:
        """Add a brain dump item to a day."""
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            day.add_brain_dump_item(command.text)

            return uow.add(day)
