"""Query to get a day template by ID."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity


class GetDayTemplateHandler:
    """Retrieves a single day template by ID."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self, user_id: UUID, day_template_id: UUID
    ) -> DayTemplateEntity:
        """Get a single day template by ID.

        Args:
            user_id: The user making the request
            day_template_id: The ID of the day template to retrieve

        Returns:
            The day template entity

        Raises:
            NotFoundError: If day template not found
        """
        async with self._uow_factory.create(user_id) as uow:
            return await uow.day_template_ro_repo.get(day_template_id)

