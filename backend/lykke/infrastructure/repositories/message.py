"""Message repository implementation."""

from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.infrastructure.database.tables import messages_tbl
from lykke.infrastructure.repositories.base.utils import (
    ensure_datetimes_utc,
    filter_init_false_fields,
    normalize_list_fields,
)

from .base import BaseRepository


class MessageRepository(BaseRepository[MessageEntity, value_objects.MessageQuery]):
    """Repository for managing Message entities.

    Note: Messages are not user-scoped directly, but are accessed through conversations.
    """

    Object = MessageEntity
    table = messages_tbl
    QueryClass = value_objects.MessageQuery

    def __init__(self, user_id: UUID | None = None) -> None:
        """Initialize MessageRepository.

        Args:
            user_id: Optional user ID for scoping (not used directly, but kept for consistency).
        """
        super().__init__(user_id=user_id)

    def build_query(self, query: value_objects.MessageQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add message-specific filtering
        if query.conversation_id is not None:
            stmt = stmt.where(self.table.c.conversation_id == query.conversation_id)

        if query.role is not None:
            stmt = stmt.where(self.table.c.role == query.role)

        return stmt

    @staticmethod
    def entity_to_row(message: MessageEntity) -> dict[str, Any]:
        """Convert a Message entity to a database row dict."""
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role.value,
            "content": message.content,
            "meta": message.meta,
            "created_at": message.created_at,
        }

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> MessageEntity:
        """Convert a database row dict to a Message entity."""
        data = normalize_list_fields(dict(row), MessageEntity)

        # Convert enum strings back to enums
        if "role" in data and isinstance(data["role"], str):
            data["role"] = value_objects.MessageRole(data["role"])

        # Ensure meta is a dict
        if data.get("meta") is None:
            data["meta"] = {}

        data = filter_init_false_fields(data, MessageEntity)
        data = ensure_datetimes_utc(data, keys=("created_at",))
        return MessageEntity(**data)
