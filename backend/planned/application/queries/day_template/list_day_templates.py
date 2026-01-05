"""Query to search day templates with pagination."""

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import DayTemplateRepositoryReadOnlyProtocol
from planned.domain import value_objects
from planned.infrastructure import data_objects


class SearchDayTemplatesHandler(BaseQueryHandler):
    """Searches day templates with pagination."""

    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.DayTemplateQuery | None = None,
    ) -> value_objects.PagedQueryResponse[data_objects.DayTemplate]:
        """Search day templates with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with day templates
        """
        if search_query is not None:
            items = await self.day_template_ro_repo.search_query(search_query)
            limit = search_query.limit or 50
            offset = search_query.offset or 0
            total = len(items)
            start = offset
            end = start + limit
            paginated_items = items[start:end]

            return value_objects.PagedQueryResponse(
                items=paginated_items,
                total=total,
                limit=limit,
                offset=offset,
                has_next=end < total,
                has_previous=start > 0,
            )
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
