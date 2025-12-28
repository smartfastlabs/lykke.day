from typing import Any
from uuid import UUID

from planned.domain.entities import Calendar

from .base import BaseQuery, BaseRepository
from .base.schema import calendars
from .base.utils import normalize_list_fields


class CalendarRepository(BaseRepository[Calendar, BaseQuery]):
    Object = Calendar
    table = calendars
    QueryClass = BaseQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize CalendarRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

    @staticmethod
    def entity_to_row(calendar: Calendar) -> dict[str, Any]:
        """Convert a Calendar entity to a database row dict."""
        row: dict[str, Any] = {
            "id": calendar.id,
            "user_uuid": calendar.user_uuid,
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
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, Calendar)
        return Calendar.model_validate(data, from_attributes=True)
