"""Query handler to get a user by phone number."""

from dataclasses import dataclass

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.utils.phone_numbers import normalize_phone_number
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity


@dataclass(frozen=True)
class GetUserByPhoneQuery(Query):
    """Query to find a user by phone number."""

    phone_number: str


class GetUserByPhoneHandler(BaseQueryHandler[GetUserByPhoneQuery, UserEntity | None]):
    """Return a user matching the phone number."""

    async def handle(self, query: GetUserByPhoneQuery) -> UserEntity | None:
        normalized = normalize_phone_number(query.phone_number)
        return await self.user_ro_repo.search_one_or_none(
            value_objects.UserQuery(phone_number=normalized)
        )
