"""Command to delete a day template."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command


@dataclass(frozen=True)
class DeleteDayTemplateCommand(Command):
    """Command to delete a day template."""

    day_template_id: UUID


class DeleteDayTemplateHandler(BaseCommandHandler[DeleteDayTemplateCommand, None]):
    """Deletes a day template."""

    async def handle(self, command: DeleteDayTemplateCommand) -> None:
        """Delete a day template.

        Args:
            command: The command containing the day template ID to delete

        Raises:
            NotFoundError: If day template not found
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(command.day_template_id)
            await uow.delete(day_template)
