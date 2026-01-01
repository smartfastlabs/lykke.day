from typing import Any
from uuid import UUID

from sqlalchemy.sql import Select

from planned.domain.entities import Event

from .base import DateQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import events_tbl


class EventRepository(UserScopedBaseRepository[Event, DateQuery]):
    Object = Event
    table = events_tbl
    QueryClass = DateQuery
    # Exclude 'date' - it's a database-only field for querying (computed from starts_at)
    excluded_row_fields = {"date"}

    def __init__(self, user_id: UUID) -> None:
        """Initialize EventRepository with user scoping."""
        super().__init__(user_id=user_id)

    def build_query(self, query: DateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        # Add date filtering if specified
        if query.date is not None:
            stmt = stmt.where(self.table.c.date == query.date)

        return stmt

    @staticmethod
    def entity_to_row(event: Event) -> dict[str, Any]:
        """Convert an Event entity to a database row dict."""
        row: dict[str, Any] = {
            "id": event.id,
            "user_id": event.user_id,
            "date": event.starts_at.date(),  # Extract date from starts_at for querying
            "name": event.name,
            "calendar_id": event.calendar_id,
            "platform_id": event.platform_id,
            "platform": event.platform,
            "status": event.status,
            "starts_at": event.starts_at,
            "frequency": event.frequency.value,
            "ends_at": event.ends_at,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }

        # Handle JSONB fields
        if event.people:
            row["people"] = [person.model_dump(mode="json") for person in event.people]

        if event.actions:
            row["actions"] = [
                action.model_dump(mode="json") for action in event.actions
            ]

        return row
