"""Command to create a brain dump."""

from dataclasses import dataclass
from datetime import date as dt_date

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import DayRepositoryReadOnlyProtocol
from lykke.application.worker_schedule import get_current_workers_to_schedule
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

    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def handle(self, command: CreateBrainDumpCommand) -> BrainDumpEntity:
        """Create a brain dump for the given date."""
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user.id)
            await self.day_ro_repo.get(day_id)

            item = BrainDumpEntity(
                user_id=self.user.id,
                date=command.date,
                text=command.text,
                status=value_objects.BrainDumpStatus.ACTIVE,
                type=value_objects.BrainDumpType.GENERAL,
            )
            item.mark_added()

            created = await uow.create(item)

            workers_to_schedule = get_current_workers_to_schedule()
            if workers_to_schedule is None:
                logger.warning(
                    f"No post-commit worker scheduler available for user {self.user.id} item {created.id}",
                )
                return created

            workers_to_schedule.schedule_process_brain_dump_item(
                user_id=self.user.id,
                day_date=command.date.isoformat(),
                item_id=created.id,
            )

            return created
