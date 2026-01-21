"""Query to get a template override by key."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TemplateRepositoryReadOnlyProtocol
from lykke.domain.entities.template import TemplateEntity
from lykke.domain.value_objects import TemplateQuery


@dataclass(frozen=True)
class GetTemplateQuery(Query):
    """Query to get a template override by key."""

    usecase: str
    key: str


class GetTemplateHandler(BaseQueryHandler[GetTemplateQuery, TemplateEntity | None]):
    """Retrieves a single template override by key."""

    template_ro_repo: TemplateRepositoryReadOnlyProtocol

    async def handle(self, query: GetTemplateQuery) -> TemplateEntity | None:
        """Get a template override by key."""
        return await self.template_ro_repo.search_one_or_none(
            TemplateQuery(usecase=query.usecase, key=query.key)
        )
