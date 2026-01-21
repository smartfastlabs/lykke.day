"""Command to delete a template override."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.template import TemplateEntity


@dataclass(frozen=True)
class DeleteTemplateCommand(Command):
    """Command to delete a template override."""

    template_id: UUID


class DeleteTemplateHandler(BaseCommandHandler[DeleteTemplateCommand, None]):
    """Deletes an existing template override."""

    async def handle(self, command: DeleteTemplateCommand) -> None:
        """Delete a template override."""
        async with self.new_uow() as uow:
            template = await uow.template_ro_repo.get(command.template_id)
            await uow.delete(template)
