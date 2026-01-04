"""Query to get a day template by ID."""

from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain.entities import DayTemplateEntity


class GetDayTemplateHandler:
    """Retrieves a single day template by ID."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

    async def run(self, day_template_id: UUID) -> DayTemplateEntity:
        """Get a single day template by ID.

        Args:
            day_template_id: The ID of the day template to retrieve

        Returns:
            The day template entity

        Raises:
            NotFoundError: If day template not found
        """
        return await self._ro_repos.day_template_ro_repo.get(day_template_id)
