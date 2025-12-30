from typing import Any
from uuid import UUID

from planned.domain.entities import Day

from .base import BaseQuery, UserScopedBaseRepository
from planned.infrastructure.database.tables import days_tbl
from .base.utils import normalize_list_fields


class DayRepository(UserScopedBaseRepository[Day, BaseQuery]):
    Object = Day
    table = days_tbl
    QueryClass = BaseQuery

    def __init__(self, user_uuid: UUID) -> None:
        """Initialize DayRepository with user scoping."""
        super().__init__(user_uuid=user_uuid)

    @staticmethod
    def entity_to_row(day: Day) -> dict[str, Any]:
        """Convert a Day entity to a database row dict."""
        row: dict[str, Any] = {
            "uuid": day.uuid,
            "user_uuid": day.user_uuid,
            "date": day.date,
            "template_uuid": day.template_uuid,
            "status": day.status.value,
            "scheduled_at": day.scheduled_at,
        }

        # Handle JSONB fields
        if day.tags:
            row["tags"] = [tag.value for tag in day.tags]

        if day.alarm:
            row["alarm"] = day.alarm.model_dump(mode="json")

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> Day:
        """Convert a database row dict to a Day entity."""
        data = dict(row)

        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(data, Day)

        return Day.model_validate(data, from_attributes=True)
