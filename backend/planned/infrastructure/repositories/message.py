from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import Message

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import messages_tbl


class MessageRepository(UserScopedBaseRepository[Message, DateQuery]):
    Object = Message
    table = messages_tbl
    QueryClass = DateQuery
    # Exclude 'date' - it's a database-only field for querying (computed from sent_at)
    excluded_row_fields = {"date"}

    def __init__(self, user_id: UUID) -> None:
        """Initialize MessageRepository with user scoping."""
        super().__init__(user_id=user_id)

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
            "user_id": message.user_id,
            "date": message.sent_at.date(),  # Extract date from sent_at for querying
            "author": message.author,
            "sent_at": message.sent_at,
            "content": message.content,
            "read_at": message.read_at,
        }

        return row
