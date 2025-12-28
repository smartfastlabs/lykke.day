from typing import Any

from planned.domain.entities import Message

from .base import BaseDateRepository
from .base.schema import messages
from .base.utils import normalize_list_fields


class MessageRepository(BaseDateRepository[Message]):
    Object = Message
    table = messages

    @staticmethod
    def entity_to_row(message: Message) -> dict[str, Any]:
        """Convert a Message entity to a database row dict."""
        row: dict[str, Any] = {
            "id": message.id,
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
