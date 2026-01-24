"""Query to search day templates with pagination."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import DayTemplateRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity


@dataclass(frozen=True)
class SearchDayTemplatesQuery(Query):
    """Query to search day templates."""

    search_query: value_objects.DayTemplateQuery | None = None


class SearchDayTemplatesHandler(
    BaseQueryHandler[
        SearchDayTemplatesQuery, value_objects.PagedQueryResponse[DayTemplateEntity]
    ]
):
    """Searches day templates with pagination."""

    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def handle(
        self, query: SearchDayTemplatesQuery
    ) -> value_objects.PagedQueryResponse[DayTemplateEntity]:
        """Search day templates with pagination.

        Args:
            query: The query containing optional search/filter query object

        Returns:
            PagedQueryResponse with day templates
        """
        if query.search_query is not None:
            result = await self.day_template_ro_repo.paged_search(query.search_query)
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
