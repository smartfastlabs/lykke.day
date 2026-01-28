"""BotPersonality repository implementation."""

from typing import Any

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import BotPersonalityEntity
from lykke.infrastructure.database.tables import bot_personalities_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import UserScopedBaseRepository


class BotPersonalityRepository(
    UserScopedBaseRepository[BotPersonalityEntity, value_objects.BotPersonalityQuery]
):
    """Repository for managing BotPersonality entities."""

    Object = BotPersonalityEntity
    table = bot_personalities_tbl
    QueryClass = value_objects.BotPersonalityQuery

    def build_query(self, query: value_objects.BotPersonalityQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add personality-specific filtering
        if query.name is not None:
            stmt = stmt.where(self.table.c.name == query.name)

        if query.base_bot_personality_id is not None:
            stmt = stmt.where(
                self.table.c.base_bot_personality_id == query.base_bot_personality_id
            )

        return stmt

    @staticmethod
    def entity_to_row(personality: BotPersonalityEntity) -> dict[str, Any]:
        """Convert a BotPersonality entity to a database row dict."""
        return {
            "id": personality.id,
            "user_id": personality.user_id,
            "name": personality.name,
            "base_bot_personality_id": personality.base_bot_personality_id,
            "system_prompt": personality.system_prompt,
            "user_amendments": personality.user_amendments,
            "meta": personality.meta,
            "created_at": personality.created_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> BotPersonalityEntity:
        """Convert a database row dict to a BotPersonality entity."""
        data = normalize_list_fields(dict(row), BotPersonalityEntity)

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        # Ensure user_amendments is a string
        if data.get("user_amendments") is None:
            data["user_amendments"] = ""

        data = filter_init_false_fields(data, BotPersonalityEntity)
        data = ensure_datetimes_utc(data, keys=("created_at",))
        return BotPersonalityEntity(**data)
