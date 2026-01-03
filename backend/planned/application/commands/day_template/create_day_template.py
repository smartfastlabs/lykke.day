"""Command to create a new day template."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity


class CreateDayTemplateHandler:
    """Creates a new day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def create_day_template(
        self, user_id: UUID, day_template: DayTemplateEntity
    ) -> DayTemplateEntity:
        """Create a new day template.

        Args:
            user_id: The user making the request
            day_template: The day template entity to create

        Returns:
            The created day template entity
        """
        async with self._uow_factory.create(user_id) as uow:
            created_day_template = await uow.day_templates.put(day_template)
            await uow.commit()
            return created_day_template

