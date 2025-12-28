from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import Message

from .base import BaseRepository, DateQuery
from .base.schema import messages
from .base.utils import normalize_list_fields


class MessageRepository(BaseRepository[Message, DateQuery]):
    Object = Message
    table = messages
    QueryClass = DateQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize MessageRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

    def build_query(self, query: DateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        return stmt

    @staticmethod
    def entity_to_row(message: Message) -> dict[str, Any]:
        """Convert a Message entity to a database row dict."""
        row: dict[str, Any] = {
            "id": message.id,
            "user_uuid": message.user_uuid,
            "date": message.sent_at.date(),  # Extract date from sent_at for querying
            "author": message.author,
            "sent_at": message.sent_at,
            "content": message.content,
            "read_at": message.read_at,
        }

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Message:
        """Convert a database row dict to a Message entity."""
        # Remove 'date' field - it's database-only for querying
        # The entity computes date from sent_at
        data = {k: v for k, v in row.items() if k != "date"}

        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(data, Message)

        return Message.model_validate(data, from_attributes=True)
