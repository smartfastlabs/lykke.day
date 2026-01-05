"""Command to delete a calendar."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteCalendarHandler:
    """Deletes a calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(self, calendar_id: UUID) -> None:
        """Delete a calendar.

        Args:
            calendar_id: The ID of the calendar to delete

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            calendar = await uow.calendar_ro_repo.get(calendar_id)
            calendar.delete()  # Mark for deletion
            uow.add(calendar)

