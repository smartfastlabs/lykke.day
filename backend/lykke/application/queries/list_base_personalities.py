"""Query to list base personality templates."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.utils.templates import list_base_personalities


@dataclass(frozen=True)
class ListBasePersonalitiesQuery(Query):
    """List available base personalities."""


@dataclass(frozen=True)
class BasePersonalityInfo:
    """Base personality descriptor."""

    slug: str
    label: str


class ListBasePersonalitiesHandler(
    BaseQueryHandler[ListBasePersonalitiesQuery, list[BasePersonalityInfo]]
):
    """Return available base personalities from templates."""

    async def handle(
        self, query: ListBasePersonalitiesQuery
    ) -> list[BasePersonalityInfo]:
        personalities = list_base_personalities()
        return [BasePersonalityInfo(**personality) for personality in personalities]
