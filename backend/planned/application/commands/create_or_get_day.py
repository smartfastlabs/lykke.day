"""Command to get an existing day or create a new one."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain.entities import Day

from .base import Command, CommandHandler


@dataclass(frozen=True)
class CreateOrGetDayCommand(Command):
    """Command to get an existing day or create a new one if it doesn't exist."""

    user_id: UUID
    date: date


class CreateOrGetDayHandler(CommandHandler[CreateOrGetDayCommand, Day]):
    """Handles CreateOrGetDayCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: CreateOrGetDayCommand) -> Day:
        """Get an existing day or create a new one.

        Args:
            cmd: The create or get command

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            day_id = Day.id_from_date_and_user(cmd.date, cmd.user_id)
            try:
                return await uow.days.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.users.get(cmd.user_id)
                template_slug = user.settings.template_defaults[cmd.date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = Day.create_for_date(
                    cmd.date,
                    user_id=cmd.user_id,
                    template=template,
                )
                result = await uow.days.put(day)
                await uow.commit()
                return result

