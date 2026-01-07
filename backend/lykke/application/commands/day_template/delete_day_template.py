"""Command to delete a day template."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler


class DeleteDayTemplateHandler(BaseCommandHandler):
    """Deletes a day template."""

    async def run(self, day_template_id: UUID) -> None:
        """Delete a day template.

        Args:
            day_template_id: The ID of the day template to delete

        Raises:
            NotFoundError: If day template not found
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            await uow.delete(day_template)
