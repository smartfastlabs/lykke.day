"""Command to delete a day template."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteDayTemplateHandler:
    """Deletes a day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(self, user_id: UUID, day_template_id: UUID) -> None:
        """Delete a day template.

        Args:
            user_id: The user making the request
            day_template_id: The ID of the day template to delete

        Raises:
            NotFoundError: If day template not found
        """
        async with self._uow_factory.create(user_id) as uow:
            day_template = await uow.day_templates.get(day_template_id)
            await uow.day_templates.delete(day_template)
            await uow.commit()

