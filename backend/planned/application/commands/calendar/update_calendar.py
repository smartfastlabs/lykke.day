"""Command to update an existing calendar."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.application.repositories import CalendarRepositoryReadOnlyProtocol
from planned.domain.entities import CalendarEntity
from planned.domain.events.calendar_events import CalendarUpdatedEvent
from planned.domain.value_objects import CalendarUpdateObject


class UpdateCalendarHandler(BaseCommandHandler):
    """Updates an existing calendar."""

    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

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
        async with self.new_uow() as uow:
            # Get the existing calendar
            calendar = await uow.calendar_ro_repo.get(calendar_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(calendar)
            return calendar

