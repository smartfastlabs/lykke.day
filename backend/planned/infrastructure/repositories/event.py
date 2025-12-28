from typing import Any

from sqlalchemy.sql import Select

from planned.domain.entities import Event

from .base import BaseRepository, DateQuery
from .base.schema import events
from .base.utils import normalize_list_fields


class EventRepository(BaseRepository[Event, DateQuery]):
    Object = Event
    table = events
    QueryClass = DateQuery

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

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Event:
        """Convert a database row dict to an Event entity."""
        # Remove 'date' field - it's database-only for querying
        # The entity computes date from starts_at
        data = {k: v for k, v in row.items() if k != "date"}

        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(data, Event)

        return Event.model_validate(data, from_attributes=True)
