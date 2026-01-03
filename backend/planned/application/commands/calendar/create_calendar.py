"""Command to create a new calendar."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity


class CreateCalendarHandler:
    """Creates a new calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, calendar: CalendarEntity
    ) -> CalendarEntity:
        """Create a new calendar.

        Args:
            user_id: The user making the request
            calendar: The calendar entity to create

        Returns:
            The created calendar entity
        """
        async with self._uow_factory.create(user_id) as uow:
            created_calendar = await uow.calendar_rw_repo.put(calendar)
            await uow.commit()
            return created_calendar

