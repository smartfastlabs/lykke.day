"""Query to list template overrides."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import TemplateRepositoryReadOnlyProtocol
from lykke.domain.entities.template import TemplateEntity
from lykke.domain.value_objects import TemplateQuery


@dataclass(frozen=True)
class ListTemplatesQuery(Query):
    """Query to list template overrides."""

    usecase: str | None = None

class ListTemplatesHandler(BaseQueryHandler[ListTemplatesQuery, list[TemplateEntity]]):
    """Lists template overrides for the current user."""

    template_ro_repo: TemplateRepositoryReadOnlyProtocol

    async def handle(self, query: ListTemplatesQuery) -> list[TemplateEntity]:
        """List template overrides for the current user."""
        return await self.template_ro_repo.search(TemplateQuery(usecase=query.usecase))
