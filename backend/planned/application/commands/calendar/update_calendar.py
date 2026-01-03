"""Command to update an existing calendar."""

from dataclasses import asdict, fields, replace
from typing import Any, cast
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity


class UpdateCalendarHandler:
    """Updates an existing calendar."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, calendar_id: UUID, calendar_data: CalendarEntity
    ) -> CalendarEntity:
        """Update an existing calendar.

        Args:
            user_id: The user making the request
            calendar_id: The ID of the calendar to update
            calendar_data: The updated calendar data

        Returns:
            The updated calendar entity

        Raises:
            NotFoundError: If calendar not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get existing calendar
            existing = await uow.calendars.get(calendar_id)

            # Merge updates - both entities are dataclasses
            # Get all fields from calendar_data that are not None
            calendar_data_dict: dict[str, Any] = asdict(calendar_data)

            # Filter out init=False fields (like _domain_events) - they can't be specified in replace()
            init_false_fields = {f.name for f in fields(existing) if not f.init}
            update_dict = {
                k: v
                for k, v in calendar_data_dict.items()
                if v is not None and k not in init_false_fields
            }
            updated_any: Any = replace(existing, **update_dict)
            updated = cast(CalendarEntity, updated_any)

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", calendar_id)

            calendar = await uow.calendars.put(updated)
            await uow.commit()
            return calendar

