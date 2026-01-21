"""Command to create a new template override."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.template import TemplateEntity


@dataclass(frozen=True)
class CreateTemplateCommand(Command):
    """Command to create a new template override."""

    template: TemplateEntity


class CreateTemplateHandler(BaseCommandHandler[CreateTemplateCommand, TemplateEntity]):
    """Creates a new template override."""

    async def handle(self, command: CreateTemplateCommand) -> TemplateEntity:
        """Create a new template override."""
        async with self.new_uow() as uow:
            return await uow.create(command.template)
