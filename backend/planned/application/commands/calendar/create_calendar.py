"""Command to create a new calendar."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity


class CreateCalendarHandler:
    """Creates a new calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(self, calendar: CalendarEntity) -> CalendarEntity:
        """Create a new calendar.

        Args:
            calendar: The calendar entity to create

        Returns:
            The created calendar entity
        """
        async with self._uow_factory.create(self.user_id) as uow:
            calendar.create()  # Mark as newly created
            uow.add(calendar)
            return calendar
