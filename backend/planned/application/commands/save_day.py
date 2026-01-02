"""Command to save a day to the database."""

from dataclasses import dataclass
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import Day

from .base import Command, CommandHandler


@dataclass(frozen=True)
class SaveDayCommand(Command):
    """Command to save a day to the database."""

    user_id: UUID
    day: Day


class SaveDayHandler(CommandHandler[SaveDayCommand, Day]):
    """Handles SaveDayCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: SaveDayCommand) -> Day:
        """Save a day to the database.

        Args:
            cmd: The save command

        Returns:
            The saved Day entity
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            await uow.days.put(cmd.day)
            await uow.commit()
            return cmd.day

