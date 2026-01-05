"""Query to search messages with pagination."""

from planned.application.queries.base import BaseQueryHandler
from planned.application.repositories import MessageRepositoryReadOnlyProtocol
from planned.domain import value_objects
from planned.domain.entities import MessageEntity


class SearchMessagesHandler(BaseQueryHandler):
    """Searches messages with pagination."""

    message_ro_repo: MessageRepositoryReadOnlyProtocol

    async def run(
        self,
        search_query: value_objects.MessageQuery | None = None,
    ) -> value_objects.PagedQueryResponse[MessageEntity]:
        """Search messages with pagination.

        Args:
            search_query: Optional search/filter query object with pagination info

        Returns:
            PagedQueryResponse with messages
        """
        if search_query is not None:
            items = await self.message_ro_repo.search_query(search_query)
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
            items = await self.message_ro_repo.all()
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

