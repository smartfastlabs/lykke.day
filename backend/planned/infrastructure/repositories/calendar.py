from typing import Any
from uuid import UUID

from planned.domain import entities

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import calendars_tbl


class CalendarRepository(UserScopedBaseRepository[entities.Calendar, BaseQuery]):
    Object = entities.Calendar
    table = calendars_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize CalendarRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(calendar: entities.Calendar) -> dict[str, Any]:
        """Convert a Calendar entity to a database row dict."""
        row: dict[str, Any] = {
            "id": calendar.id,
            "user_id": calendar.user_id,
            "name": calendar.name,
            "auth_token_id": calendar.auth_token_id,
            "platform_id": calendar.platform_id,
            "platform": calendar.platform,
            "last_sync_at": calendar.last_sync_at,
        }

        return row
