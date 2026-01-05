"""Command to update an existing calendar."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity
from planned.domain.events.calendar_events import CalendarUpdatedEvent
from planned.domain.value_objects import CalendarUpdateObject


class UpdateCalendarHandler:
    """Updates an existing calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self, calendar_id: UUID, update_data: CalendarUpdateObject
    ) -> CalendarEntity:
        """Update an existing calendar.

        Args:
            calendar_id: The ID of the calendar to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            # Get the existing calendar
            calendar = await uow.calendar_ro_repo.get(calendar_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(calendar)
            return calendar

