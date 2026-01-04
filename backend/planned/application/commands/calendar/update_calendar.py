"""Command to update an existing calendar."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity
from planned.domain.value_objects import CalendarUpdateObject


class UpdateCalendarHandler:
    """Updates an existing calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, calendar_id: UUID, update_data: CalendarUpdateObject
    ) -> CalendarEntity:
        """Update an existing calendar.

        Args:
            user_id: The user making the request
            calendar_id: The ID of the calendar to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Convert update_data to dict and filter out None values
            update_data_dict: dict[str, Any] = asdict(update_data)
            update_dict = {k: v for k, v in update_data_dict.items() if v is not None}

            # Apply updates directly to the database
            calendar = await uow.calendar_rw_repo.apply_updates(calendar_id, **update_dict)
            await uow.commit()
            return calendar

