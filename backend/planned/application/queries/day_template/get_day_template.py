"""Query to get a day template by ID."""

from uuid import UUID

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import DayTemplateRepositoryReadOnlyProtocol
from planned.domain.entities.day_template import DayTemplateEntity


class GetDayTemplateHandler(BaseQueryHandler):
    """Retrieves a single day template by ID."""

    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def run(self, day_template_id: UUID) -> DayTemplateEntity:
        """Get a single day template by ID.

        Args:
            day_template_id: The ID of the day template to retrieve

        Returns:
            The day template data object

        Raises:
            NotFoundError: If day template not found
        """
        return await self.day_template_ro_repo.get(day_template_id)
