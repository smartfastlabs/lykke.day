"""Query handler for getting usecase config."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities.usecase_config import UseCaseConfigEntity


@dataclass(frozen=True)
class GetUseCaseConfigQuery(Query):
    """Query to get a usecase config by usecase key."""

    usecase: str


class GetUseCaseConfigHandler(
    BaseQueryHandler[GetUseCaseConfigQuery, UseCaseConfigEntity | None]
):
    """Handler for getting a usecase config."""

    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol

    async def handle(self, query: GetUseCaseConfigQuery) -> UseCaseConfigEntity | None:
        """Get usecase config by usecase key."""
        configs = await self.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=query.usecase)
        )
        return configs[0] if configs else None
