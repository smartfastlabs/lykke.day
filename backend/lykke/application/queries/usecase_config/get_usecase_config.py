"""Query handler for getting usecase config."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.domain.entities.usecase_config import UseCaseConfigEntity
from lykke.domain import value_objects


@dataclass(frozen=True)
class GetUseCaseConfigQuery(Query):
    """Query to get a usecase config by usecase key."""

    usecase: str


class GetUseCaseConfigHandler(
    BaseQueryHandler[GetUseCaseConfigQuery, UseCaseConfigEntity | None]
):
    """Handler for getting a usecase config."""

    async def handle(self, query: GetUseCaseConfigQuery) -> UseCaseConfigEntity | None:
        """Get usecase config by usecase key."""
        configs = await self._ro_repos.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=query.usecase)
        )
        return configs[0] if configs else None
