"""BotPersonality repository implementation."""

from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.entities import BotPersonalityEntity
from lykke.infrastructure.database.tables import bot_personalities_tbl
from sqlalchemy.sql import Select

from .base import BaseRepository


class BotPersonalityRepository(
    BaseRepository[BotPersonalityEntity, value_objects.BotPersonalityQuery]
):
    """Repository for managing BotPersonality entities.

    Note: BotPersonalities can be user-scoped (user_id set) or system-wide (user_id is None).
    The user_id on the repository is optional to support querying both.
    """

    Object = BotPersonalityEntity
    table = bot_personalities_tbl
    QueryClass = value_objects.BotPersonalityQuery

    def __init__(self, user_id: UUID | None = None) -> None:
        """Initialize BotPersonalityRepository with optional user scoping.

        Args:
            user_id: Optional user ID. When set, queries will include both user-specific
                    and system-wide (user_id=None) personalities.
        """
        super().__init__(user_id=user_id)

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

        # When user_id is set on the repository, allow both user-specific and system-wide
        if self._is_user_scoped:
            stmt = stmt.where(
                (self.table.c.user_id == self.user_id) | (self.table.c.user_id.is_(None))
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
        from lykke.infrastructure.repositories.base.utils import (
            ensure_datetimes_utc,
            filter_init_false_fields,
            normalize_list_fields,
        )

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
