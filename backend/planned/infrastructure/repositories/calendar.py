from typing import Any

from planned.domain.entities import Calendar

from .base import BaseCrudRepository
from .base.schema import calendars


class CalendarRepository(BaseCrudRepository[Calendar]):
    Object = Calendar
    table = calendars

    @staticmethod
    def entity_to_row(calendar: Calendar) -> dict[str, Any]:
        """Convert a Calendar entity to a database row dict."""
        row: dict[str, Any] = {
            "id": calendar.id,
            "name": calendar.name,
            "auth_token_id": calendar.auth_token_id,
            "platform_id": calendar.platform_id,
            "platform": calendar.platform,
            "last_sync_at": calendar.last_sync_at,
        }

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Calendar:
        """Convert a database row dict to a Calendar entity."""
        return Calendar.model_validate(row, from_attributes=True)
