"""Command to create a new day template."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class CreateDayTemplateCommand(Command):
    """Command to create a new day template."""

    day_template: DayTemplateEntity


class CreateDayTemplateHandler(
    BaseCommandHandler[CreateDayTemplateCommand, DayTemplateEntity]
):
    """Creates a new day template."""

    async def handle(self, command: CreateDayTemplateCommand) -> DayTemplateEntity:
        """Create a new day template.

        Args:
            command: The command containing the day template entity to create

        Returns:
            The created day template entity
        """
        async with self.new_uow() as uow:
            return await uow.create(command.day_template)
