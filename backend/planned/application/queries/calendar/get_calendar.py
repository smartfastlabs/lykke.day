"""Query to get a calendar by ID."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity


class GetCalendarHandler:
    """Retrieves a single calendar by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(self, user_id: UUID, calendar_id: UUID) -> CalendarEntity:
        """Get a single calendar by ID.

        Args:
            user_id: The user making the request
            calendar_id: The ID of the calendar to retrieve

        Returns:
            The calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(user_id) as uow:
            return await uow.calendar_ro_repo.get(calendar_id)

