"""Command to create a new day template."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity


class CreateDayTemplateHandler:
    """Creates a new day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def run(
        self, day_template: DayTemplateEntity
    ) -> DayTemplateEntity:
        """Create a new day template.

        Args:
            day_template: The day template entity to create

        Returns:
            The created day template entity
        """
        async with self._uow_factory.create(self.user_id) as uow:
            await uow.create(day_template)
            return day_template

