"""Query to search day templates with pagination."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.application.repositories import DayTemplateRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity


class SearchDayTemplatesHandler(BaseQueryHandler):
    """Searches day templates with pagination."""

    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.DayTemplateQuery | None = None,
    ) -> value_objects.PagedQueryResponse[DayTemplateEntity]:
        """Search day templates with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with day templates
        """
        if search_query is not None:
            result = await self.day_template_ro_repo.paged_search(search_query)
            return result
        else:
            items = await self.day_template_ro_repo.all()
            total = len(items)
            limit = 50
            offset = 0

            return value_objects.PagedQueryResponse(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
                has_next=False,
                has_previous=False,
            )
