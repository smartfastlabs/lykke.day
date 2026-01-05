"""Command to update an existing day template."""

from dataclasses import asdict
from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.value_objects import DayTemplateUpdateObject
from planned.infrastructure import data_objects


class UpdateDayTemplateHandler(BaseCommandHandler):
    """Updates an existing day template."""

    async def run(
        self,
        day_template_id: UUID,
        update_data: DayTemplateUpdateObject,
    ) -> data_objects.DayTemplate:
        """Update an existing day template.

        Args:
            day_template_id: The ID of the day template to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated day template data object

        Raises:
            NotFoundError: If day template not found
        """
        async with self.new_uow() as uow:
            # Get the existing day template
            day_template = await uow.day_template_ro_repo.get(day_template_id)

            # Convert update object to dict and filter out None values
            update_dict = asdict(update_data)
            update_dict = {k: v for k, v in update_dict.items() if v is not None}

            # Apply updates using clone
            updated_day_template = day_template.clone(**update_dict)

            # Add to UoW for saving
            uow.add(updated_day_template)
            return updated_day_template
