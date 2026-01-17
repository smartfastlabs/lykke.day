"""Query to get a day template by ID."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import DayTemplateRepositoryReadOnlyProtocol
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class GetDayTemplateQuery(Query):
    """Query to get a day template by ID."""

    day_template_id: UUID


class GetDayTemplateHandler(BaseQueryHandler[GetDayTemplateQuery, DayTemplateEntity]):
    """Retrieves a single day template by ID."""

    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def handle(self, query: GetDayTemplateQuery) -> DayTemplateEntity:
        """Get a single day template by ID.

        Args:
            query: The query containing the day template ID

        Returns:
            The day template entity

        Raises:
            NotFoundError: If day template not found
        """
        return await self.day_template_ro_repo.get(query.day_template_id)
