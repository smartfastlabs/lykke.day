"""Conversation repository implementation."""

from typing import Any

from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity
from lykke.infrastructure.database.tables import conversations_tbl
from sqlalchemy.sql import Select

from .base import UserScopedBaseRepository


class ConversationRepository(
    UserScopedBaseRepository[ConversationEntity, value_objects.ConversationQuery]
):
    """Repository for managing Conversation entities."""

    Object = ConversationEntity
    table = conversations_tbl
    QueryClass = value_objects.ConversationQuery

    def build_query(self, query: value_objects.ConversationQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add conversation-specific filtering
        if query.channel is not None:
            stmt = stmt.where(self.table.c.channel == query.channel)

        if query.status is not None:
            stmt = stmt.where(self.table.c.status == query.status)

        if query.bot_personality_id is not None:
            stmt = stmt.where(self.table.c.bot_personality_id == query.bot_personality_id)

        return stmt

    @staticmethod
    def entity_to_row(conversation: ConversationEntity) -> dict[str, Any]:
        """Convert a Conversation entity to a database row dict."""
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "bot_personality_id": conversation.bot_personality_id,
            "channel": conversation.channel.value,
            "status": conversation.status.value,
            "llm_provider": conversation.llm_provider.value,
            "context": conversation.context,
            "created_at": conversation.created_at,
            "last_message_at": conversation.last_message_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> ConversationEntity:
        """Convert a database row dict to a Conversation entity."""
        from lykke.infrastructure.repositories.base.utils import (
            ensure_datetimes_utc,
            filter_init_false_fields,
            normalize_list_fields,
        )

        data = normalize_list_fields(dict(row), ConversationEntity)

        # Convert enum strings back to enums
        if "channel" in data and isinstance(data["channel"], str):
            data["channel"] = value_objects.ConversationChannel(data["channel"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = value_objects.ConversationStatus(data["status"])
        if "llm_provider" in data and isinstance(data["llm_provider"], str):
            data["llm_provider"] = value_objects.LLMProvider(data["llm_provider"])

        # Ensure context is a dict
        if data.get("context") is None:
            data["context"] = {}

        data = filter_init_false_fields(data, ConversationEntity)
        data = ensure_datetimes_utc(data, keys=("created_at", "last_message_at"))
        return ConversationEntity(**data)
