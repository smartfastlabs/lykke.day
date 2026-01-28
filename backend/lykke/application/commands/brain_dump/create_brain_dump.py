"""Command to create a brain dump."""

from dataclasses import dataclass
from datetime import date as dt_date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity, DayEntity


@dataclass(frozen=True)
class CreateBrainDumpCommand(Command):
    """Command to create a brain dump."""

    date: dt_date
    text: str


class CreateBrainDumpHandler(
    BaseCommandHandler[CreateBrainDumpCommand, BrainDumpEntity]
):
    """Creates a brain dump."""

    async def handle(self, command: CreateBrainDumpCommand) -> BrainDumpEntity:
        """Create a brain dump for the given date."""
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            await uow.day_ro_repo.get(day_id)

            item = BrainDumpEntity(
                user_id=self.user_id,
                date=command.date,
                text=command.text,
                status=value_objects.BrainDumpStatus.ACTIVE,
                type=value_objects.BrainDumpType.GENERAL,
            )
            item.mark_added()

            return await uow.create(item)
