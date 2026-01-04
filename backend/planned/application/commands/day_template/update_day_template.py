"""Command to update an existing day template."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity
from planned.domain.value_objects import DayTemplateUpdateObject


class UpdateDayTemplateHandler:
    """Updates an existing day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self,
        day_template_id: UUID,
        update_data: DayTemplateUpdateObject,
    ) -> DayTemplateEntity:
        """Update an existing day template.

        Args:
            day_template_id: The ID of the day template to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated day template entity

        Raises:
            NotFoundError: If day template not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            # Convert update_data to dict and filter out None values
            update_data_dict: dict[str, Any] = asdict(update_data)
            update_dict = {k: v for k, v in update_data_dict.items() if v is not None}

            # Apply updates directly to the database
            day_template = await uow.day_template_rw_repo.apply_updates(
                day_template_id, **update_dict
            )
            await uow.commit()
            return day_template

