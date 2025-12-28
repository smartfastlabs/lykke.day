from typing import Any

from planned.domain.entities import Event

from .base import BaseDateRepository
from .base.schema import events


class EventRepository(BaseDateRepository[Event]):
    Object = Event
    table = events

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
            row["people"] = [person.model_dump() for person in event.people]

        if event.actions:
            row["actions"] = [action.model_dump() for action in event.actions]

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Event:
        """Convert a database row dict to an Event entity."""
        # Remove 'date' field - it's database-only for querying
        # The entity computes date from starts_at
        data = {k: v for k, v in row.items() if k != "date"}

        return Event.model_validate(data, from_attributes=True)
