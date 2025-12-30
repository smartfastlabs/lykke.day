from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import select

from planned.core.exceptions import exceptions
from planned.domain.entities import Calendar

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import calendars_tbl
from .base.utils import normalize_list_fields


class CalendarRepository(UserScopedBaseRepository[Calendar, BaseQuery]):
    Object = Calendar
    table = calendars_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize CalendarRepository with user scoping."""
        super().__init__(user_id=user_id)


    @staticmethod
    def entity_to_row(calendar: Calendar) -> dict[str, Any]:
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

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Calendar:
        """Convert a database row dict to a Calendar entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, Calendar)
        return Calendar.model_validate(data, from_attributes=True)
