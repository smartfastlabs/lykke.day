"""Command to update an existing day template."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity
from planned.domain.events.day_template_events import DayTemplateUpdatedEvent
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
            # Get the existing day template
            day_template = await uow.day_template_ro_repo.get(day_template_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            day_template = day_template.apply_update(
                update_data, DayTemplateUpdatedEvent
            )

            # Add entity to UoW for saving
            uow.add(day_template)
            return day_template
