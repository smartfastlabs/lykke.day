"""Command to delete a calendar."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler


class DeleteCalendarHandler(BaseCommandHandler):
    """Deletes a calendar."""

    async def run(self, calendar_id: UUID) -> None:
        """Delete a calendar.

        Args:
            calendar_id: The ID of the calendar to delete

        Raises:
            NotFoundError: If calendar not found
        """
        async with self.new_uow() as uow:
            calendar = await uow.calendar_ro_repo.get(calendar_id)
            await uow.delete(calendar)

