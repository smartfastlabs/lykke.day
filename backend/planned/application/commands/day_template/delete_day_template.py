"""Command to delete a day template."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory


class DeleteDayTemplateHandler:
    """Deletes a day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(self, day_template_id: UUID) -> None:
        """Delete a day template.

        Args:
            day_template_id: The ID of the day template to delete

        Raises:
            NotFoundError: If day template not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            await uow.delete(day_template)
