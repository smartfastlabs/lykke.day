"""Command to delete a calendar."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteCalendarHandler:
    """Deletes a calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(self, user_id: UUID, calendar_id: UUID) -> None:
        """Delete a calendar.

        Args:
            user_id: The user making the request
            calendar_id: The ID of the calendar to delete

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(user_id) as uow:
            calendar = await uow.calendar_rw_repo.get(calendar_id)
            await uow.calendar_rw_repo.delete(calendar)
            await uow.commit()

